let selectedTimes = [];
const pricePerHour = 700;

function selectTimeSlot(button, startTime, endTime) {
    // ถ้าปุ่มถูก disable หรือจองแล้ว ให้ return
    if (button.disabled || button.classList.contains('bg-red-500')) {
        return;
    }

    // สลับสีปุ่ม
    if (button.classList.contains('bg-green-500')) {
        // เลือกเวลา
        button.classList.remove('bg-green-500');
        button.classList.add('bg-yellow-500');
        selectedTimes.push({
            start: startTime,
            end: endTime,
            button: button
        });
    } else if (button.classList.contains('bg-yellow-500')) {
        // ยกเลิกการเลือก
        button.classList.remove('bg-yellow-500');
        button.classList.add('bg-green-500');
        selectedTimes = selectedTimes.filter(t => t.start !== startTime);
    }

    updateBookingDisplay();
}

function updateBookingDisplay() {
    const timeRangeElement = document.getElementById('selectedTimeRange');
    const totalPriceElement = document.getElementById('totalPrice');
    const bookingButton = document.getElementById('bookingButton');

    if (selectedTimes.length > 0) {
        // เรียงลำดับเวลา
        selectedTimes.sort((a, b) => parseFloat(a.start) - parseFloat(b.start));

        // หาเวลาเริ่มต้นและสิ้นสุดรวม
        const firstTime = selectedTimes[0];
        const lastTime = selectedTimes[selectedTimes.length - 1];
        
        // แสดงช่วงเวลา
        timeRangeElement.textContent = 
            `${firstTime.start} - ${lastTime.end} (${selectedTimes.length} ชั่วโมง)`;

        // คำนวณราคารวม
        const totalPrice = selectedTimes.length * pricePerHour;
        totalPriceElement.textContent = `${totalPrice.toLocaleString()} บาท`;

        // เปิดปุ่มจอง
        bookingButton.disabled = false;
    } else {
        // รีเซ็ตการแสดงผล
        timeRangeElement.textContent = '-';
        totalPriceElement.textContent = '-';
        bookingButton.disabled = true;
    }
}

async function submitBooking() {
    const customerName = document.getElementById('reserverName').value;
    const phone = document.getElementById('reseverPhone').value;

    if (!customerName || !phone || selectedTimes.length === 0) {
        alert('กรุณากรอกข้อมูลให้ครบถ้วน');
        return;
    }

    try {
        // เปลี่ยนทุกปุ่มที่เลือกเป็นสีแดง
        selectedTimes.forEach(time => {
            const button = time.button;
            button.classList.remove('bg-yellow-500');
            button.classList.add('bg-red-500');
            button.disabled = true;
        });

        alert('จองสำเร็จ!');

        // รีเซ็ตฟอร์ม
        document.getElementById('reserverName').value = '';
        document.getElementById('reseverPhone').value = '';
        selectedTimes = [];
        updateBookingDisplay();

    } catch (error) {
        console.error('Error:', error);
        alert('เกิดข้อผิดพลาดในการจอง');
    }
}

// เพิ่ม Event Listener เมื่อโหลดหน้า
document.addEventListener('DOMContentLoaded', () => {
    // ตั้งค่าวันที่เริ่มต้นเป็นวันนี้
    const dateInput = document.getElementById('date');
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;
    dateInput.min = today;
});