// =========================================================================================
// !!! สำคัญมาก: เปลี่ยนค่านี้ให้เป็น Invocation URL จริงจาก API Gateway ของคุณ !!!
// ตัวอย่าง: "https://xxxxxx.execute-api.us-east-1.amazonaws.com/v1/students"
// =========================================================================================
const STUDENT_API_URL = "https://mikz7aou67.execute-api.us-east-1.amazonaws.com/V1/students";
// =========================================================================================

const tableBody = document.getElementById('studentTableBody');
const addStudentForm = document.getElementById('addStudentForm');
const messageBox = document.getElementById('messageBox');
const submitButton = document.getElementById('submitButton');

// ฟังก์ชันแสดงข้อความแจ้งเตือน
function showMessage(message, type = 'success') {
    messageBox.textContent = message;
    messageBox.classList.remove('hidden', 'bg-red-100', 'text-red-700', 'bg-green-100', 'text-green-700');
    
    if (type === 'error') {
        messageBox.classList.add('bg-red-100', 'text-red-700');
    } else {
        messageBox.classList.add('bg-green-100', 'text-green-700');
    }

    setTimeout(() => {
        messageBox.classList.add('hidden');
    }, 5000);
}

// ฟังก์ชันดึงข้อมูลและแสดงในตาราง
async function fetchStudents() {
    tableBody.innerHTML = `
        <tr>
            <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500">
                กำลังดึงข้อมูลจาก DynamoDB...
            </td>
        </tr>
    `;
    
    try {
        const response = await fetch(STUDENT_API_URL, {
            method: 'GET',
              credentials: "include",
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! Status: ${response.status}. Detail: ${errorText.substring(0, 100)}...`);
        }

        const students = await response.json();
        tableBody.innerHTML = ''; // เคลียร์ตารางเดิม

        if (students.length === 0) {
             tableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500">
                        ไม่พบข้อมูลนักศึกษาในระบบ
                    </td>
                </tr>
            `;
            return;
        }

        students.forEach(student => {
            const row = tableBody.insertRow();
            row.classList.add('hover:bg-gray-100', 'transition', 'duration-150');
            
            // ใช้ toLocaleString เพื่อจัดรูปแบบวันที่ให้คนอ่านง่ายขึ้น
            const formattedTimestamp = student.timestamp ? new Date(student.timestamp).toLocaleString('th-TH', { 
                year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
            }) : '-';
            
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${student.student_id}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${student.name}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${student.major}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${formattedTimestamp}</td>
            `;
        });
        
    } catch (error) {
        console.error("Failed to fetch student data:", error);
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="px-6 py-4 text-center text-sm text-red-600 bg-red-50">
                    **เกิดข้อผิดพลาดในการดึงข้อมูล**: โปรดตรวจสอบ URL ของ API Gateway และ Lambda Log
                    <div class="mt-1 text-xs text-red-500 truncate">${error.message}</div>
                </td>
            </tr>
        `;
        showMessage("ไม่สามารถดึงข้อมูลได้: โปรดตรวจสอบ API URL และสิทธิ์การเข้าถึง (IAM Role)", 'error');
    }
}

// ฟังก์ชันเพิ่มข้อมูล (Event Listener)
addStudentForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    submitButton.disabled = true;
    submitButton.textContent = 'กำลังบันทึก...';
    
    const studentData = {
        student_id: document.getElementById('student_id').value.trim(),
        name: document.getElementById('name').value.trim(),
        major: document.getElementById('major').value.trim()
    };

    try {
        const response = await fetch(STUDENT_API_URL, {
            method: 'POST',
              credentials: "include",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(studentData)
        });

        const result = await response.json();

        if (response.ok) {
            showMessage("บันทึกข้อมูลสำเร็จ!");
            addStudentForm.reset();
            fetchStudents(); // ดึงข้อมูลใหม่มาแสดง
        } else {
            // กรณี Lambda หรือ API Gateway ส่ง Status Code 4xx/5xx กลับมา
            const errorMessage = result.error || "ไม่ทราบข้อผิดพลาด";
            showMessage(`บันทึกข้อมูลไม่สำเร็จ: ${errorMessage}`, 'error');
        }
    } catch (error) {
        // กรณีเกิดข้อผิดพลาดด้านเครือข่าย/CORS
        console.error("Failed to add student data:", error);
        showMessage("เกิดข้อผิดพลาดในการเชื่อมต่อ: โปรดตรวจสอบ URL หรือ CORS", 'error');
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'บันทึกข้อมูล (Save Data)';
    }
});

// เรียกฟังก์ชันดึงข้อมูลเมื่อโหลดหน้าเว็บเสร็จ
document.addEventListener('DOMContentLoaded', fetchStudents);
