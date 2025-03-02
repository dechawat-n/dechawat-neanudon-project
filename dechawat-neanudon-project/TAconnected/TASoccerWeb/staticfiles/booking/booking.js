let selectedTimes = [];
let fieldId = null;
let pricePerHour = 0;

// เพิ่ม base URL สำหรับ API
const API_BASE_URL = '';

document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('date');
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
    dateInput.value = today;
    
    // Check availability when date changes
    dateInput.addEventListener('change', async function() {
        await checkAvailability();
    });
    
    // Initialize booking data and check availability
    initializeBooking();
    
    // Check availability every 30 seconds
    setInterval(checkAvailability, 30000);
});

function resetTimeSlots() {
    selectedTimes = [];
    const buttons = document.querySelectorAll('button[data-start]');
    buttons.forEach(button => {
        button.classList.remove('bg-yellow-500', 'bg-red-500');
        button.classList.add('bg-green-500');
        button.disabled = false;
    });
    updateBookingDisplay();
}

function selectTimeSlot(button, startTime, endTime) {
    if (button.disabled || button.classList.contains('bg-red-500')) {
        return;
    }

    if (button.classList.contains('bg-green-500')) {
        button.classList.remove('bg-green-500');
        button.classList.add('bg-yellow-500');
        selectedTimes.push({
            start: startTime,
            end: endTime,
            button: button
        });
    } else if (button.classList.contains('bg-yellow-500')) {
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
        // เรียงลำดับตามเวลา
        selectedTimes.sort((a, b) => parseFloat(a.start) - parseFloat(b.start));
        
        // สร้างข้อความแสดงช่วงเวลา
        const timeRangeText = selectedTimes.map(time => 
            `${time.start} - ${time.end}`
        ).join(' และ ');
        
        timeRangeElement.textContent = `${timeRangeText} (${selectedTimes.length} ชั่วโมง)`;
        const totalPrice = selectedTimes.length * pricePerHour;
        totalPriceElement.textContent = `${totalPrice.toLocaleString()} บาท`;
        bookingButton.disabled = false;
    } else {
        timeRangeElement.textContent = '-';
        totalPriceElement.textContent = '-';
        bookingButton.disabled = true;
    }
}

async function initializeBooking() {
    // ดึง field_id จาก URL ถ้ามี
    const urlParams = new URLSearchParams(window.location.search);
    let fieldIdFromUrl = urlParams.get('field_id');
    
    // ถ้าไม่มี field_id ใน URL ให้กำหนดตามหน้าที่กำลังเปิดอยู่
    if (!fieldIdFromUrl) {
        const currentPath = window.location.pathname;
        if (currentPath.includes('big-reservation')) {
            fieldId = "1";  // สนามใหญ่
        } else if (currentPath.includes('medium-reservation')) {
            fieldId = "2";  // สนามกลาง
        } else if (currentPath.includes('small-reservation')) {
            fieldId = "3";  // สนามเล็ก
        }
        
        // ถ้ากำหนดค่า fieldId ได้ ให้เพิ่มเข้าไปใน URL
        if (fieldId) {
            window.history.replaceState(null, '', `?field_id=${fieldId}`);
        }
    } else {
        // ถ้ามี field_id ใน URL ให้ใช้ค่านั้น
        fieldId = fieldIdFromUrl.replace('\\', '');
    }
    
    // ถ้าไม่มี field_id ให้ออกจากฟังก์ชัน
    if (!fieldId) return;

    try {
        const response = await fetch(`/api/fields/?id=${fieldId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch field data');
        }
        const fieldData = await response.json();
        const field = fieldData[0];
        
        document.querySelector('h2').textContent = `${field.name} สำหรับ ${field.capacity} คน`;
        pricePerHour = field.price_per_hour;
        
        await checkAvailability();
    } catch (error) {
        console.error('Error:', error);
    }
}

document.addEventListener('DOMContentLoaded', async function() {
    const dateInput = document.getElementById('date');
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
    dateInput.value = today;
    
    // เรียก initializeBooking ก่อน
    await initializeBooking();
    
    // จากนั้นเช็คสถานะการจอง
    await checkAvailability();
    
    // เพิ่ม event listener สำหรับการเปลี่ยนวันที่
    dateInput.addEventListener('change', async function() {
        await checkAvailability();
    });
    
    // เช็คทุก 30 วินาที
    setInterval(async () => {
        await checkAvailability();
    }, 30000);
});

async function checkAvailability() {
    const date = document.getElementById('date').value;
    if (!date || !fieldId) return;
    
    try {
        const response = await fetch(`/api/check-availability/?date=${date}&field_id=${fieldId}`);
        if (!response.ok) {
            throw new Error('Failed to check availability');
        }
        
        const data = await response.json();
        
        // เก็บ ID ของช่วงเวลาที่ถูกเลือกไว้
        const selectedTimeSlotIds = selectedTimes.map(time => 
            `${time.start}-${time.end}`
        );
        
        // รีเซ็ตเฉพาะปุ่มที่ไม่ได้เลือกไว้
        const buttons = document.querySelectorAll('button[data-start]');
        buttons.forEach(button => {
            const startTime = button.getAttribute('data-start');
            const endTime = button.getAttribute('data-end');
            const timeSlotId = `${startTime}-${endTime}`;
            
            // ตรวจสอบว่าปุ่มนี้อยู่ใน selectedTimes หรือไม่
            const isSelected = selectedTimeSlotIds.includes(timeSlotId);
            
            if (!isSelected) {
                // รีเซ็ตเฉพาะปุ่มที่ไม่ได้เลือกไว้
                button.classList.remove('bg-yellow-500', 'bg-red-500');
                button.classList.add('bg-green-500');
                button.disabled = false;
            }
        });
        
        // อัพเดทสถานะปุ่มตามข้อมูลจาก server
        if (data.time_slots) {
            data.time_slots.forEach(slot => {
                const buttonSelector = `button[data-start="${slot.start}"][data-end="${slot.end}"]`;
                const button = document.querySelector(buttonSelector);
                
                // เปลี่ยนเป็นสีแดงเฉพาะถ้าปุ่มนี้ไม่ได้ถูกเลือกไว้
                if (button && slot.status === 'reserved') {
                    const startTime = button.getAttribute('data-start');
                    const endTime = button.getAttribute('data-end');
                    const timeSlotId = `${startTime}-${endTime}`;
                    
                    const isSelected = selectedTimeSlotIds.includes(timeSlotId);
                    
                    if (!isSelected) {
                        button.classList.remove('bg-green-500', 'bg-yellow-500');
                        button.classList.add('bg-red-500');
                        button.disabled = true;
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error checking availability:', error);
    }
}

async function submitBooking(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    const customerName = document.getElementById('reserverName').value;
    const phone = document.getElementById('reseverPhone').value;
    const date = document.getElementById('date').value;
    
    if (!date) {
        alert('กรุณาเลือกวันที่');
        return;
    }
    
    if (!customerName || !phone || selectedTimes.length === 0) {
        alert('กรุณากรอกข้อมูลให้ครบถ้วน');
        return;
    }

    try {
        // เรียงลำดับเวลาที่เลือกตามลำดับ
        const sortedSelectedTimes = selectedTimes.sort((a, b) => 
            parseFloat(a.start) - parseFloat(b.start)
        );
        
        let failedBookings = [];
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // เก็บ ID ของ time slots ที่ถูกเลือก
        const selectedTimeSlotIds = selectedTimes.map(slot => 
            `${slot.start}-${slot.end}`
        );
        
        // จองเฉพาะช่วงเวลาที่เลือกเท่านั้น
        for (const timeSlot of sortedSelectedTimes) {
            const bookingData = {
                field_id: parseInt(fieldId),
                date: date,
                start_time: timeSlot.start.replace(':', '.'),
                end_time: timeSlot.end.replace(':', '.'),
                customer_name: customerName,
                phone: phone,
                total_price: pricePerHour,
                // เพิ่มการส่ง ID ของช่วงเวลาที่เลือก
                selected_time_slots: selectedTimeSlotIds
            };
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/create-reservation/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    credentials: 'include',
                    body: JSON.stringify(bookingData)
                });
                
                const result = await response.json();
                
                if (response.ok && result.status === 'success') {
                    console.log(`Booking successful for ${timeSlot.start}-${timeSlot.end}`);
                    
                    // เปลี่ยนสีปุ่มที่จองสำเร็จเป็นสีแดง
                    if (timeSlot.button) {
                        timeSlot.button.classList.remove('bg-yellow-500', 'bg-green-500');
                        timeSlot.button.classList.add('bg-red-500');
                        timeSlot.button.disabled = true;
                    }
                } else {
                    console.error('Booking failed:', result);
                    failedBookings.push({
                        timeSlot: `${timeSlot.start}-${timeSlot.end}`,
                        reason: result.message || 'การจองไม่สำเร็จ'
                    });
                }
            } catch (error) {
                console.error(`Error booking ${timeSlot.start}-${timeSlot.end}:`, error);
                failedBookings.push({
                    timeSlot: `${timeSlot.start}-${timeSlot.end}`,
                    reason: error.message
                });
            }
        }
        
        // แสดงผลการจอง
        if (failedBookings.length > 0) {
            const errorMessage = failedBookings.map(booking => 
                `เวลา ${booking.timeSlot}: ${booking.reason}`
            ).join('\n');
            
            alert(`มีบางช่วงเวลาที่จองไม่สำเร็จ:\n${errorMessage}`);
        } else {
            alert('จองสำเร็จ!');
        }
        
        // รีเซ็ตฟอร์มและการแสดงผล
        document.getElementById('reserverName').value = '';
        document.getElementById('reseverPhone').value = '';
        document.getElementById('selectedTimeRange').textContent = '-';
        document.getElementById('totalPrice').textContent = '-';
        document.getElementById('bookingButton').disabled = true;
        selectedTimes = [];

        // รีเฟรชข้อมูลการจอง
        await checkAvailability();
        
    } catch (error) {
        console.error('Error:', error);
        alert('เกิดข้อผิดพลาดในการจอง: ' + error.message);
    }
}