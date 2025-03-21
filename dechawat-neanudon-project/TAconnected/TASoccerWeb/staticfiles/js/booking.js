let selectedTimes = [];
let fieldId = null;
let pricePerHour = 0;

// เพิ่ม base URL สำหรับ API
const API_BASE_URL = 'http://127.0.0.1:8000';

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
        selectedTimes.sort((a, b) => parseFloat(a.start) - parseFloat(b.start));
        
        // แยกเป็นช่วงต่อเนื่อง
        const timeSlotGroups = groupConsecutiveTimeSlots(selectedTimes);
        
        // สร้าง string แสดงช่วงเวลา
        let timeRangeText = '';
        if (timeSlotGroups.length === 1) {
            // กรณีมีช่วงเดียว
            const firstTime = timeSlotGroups[0][0];
            const lastTime = timeSlotGroups[0][timeSlotGroups[0].length - 1];
            timeRangeText = `${firstTime.start} - ${lastTime.end} (${timeSlotGroups[0].length} ชั่วโมง)`;
        } else {
            // กรณีมีหลายช่วง
            const timeRanges = timeSlotGroups.map(group => {
                const firstTime = group[0];
                const lastTime = group[group.length - 1];
                return `${firstTime.start} - ${lastTime.end}`;
            });
            timeRangeText = timeRanges.join(', ') + ` (${selectedTimes.length} ชั่วโมง)`;
        }
        
        timeRangeElement.textContent = timeRangeText;
        const totalPrice = selectedTimes.length * pricePerHour;
        totalPriceElement.textContent = `${totalPrice.toLocaleString()} บาท`;
        bookingButton.disabled = false;
    } else {
        timeRangeElement.textContent = '-';
        totalPriceElement.textContent = '-';
        bookingButton.disabled = true;
    }
}

function groupConsecutiveTimeSlots(timeSlots) {
    if (timeSlots.length === 0) return [];
    
    // เรียงลำดับตามเวลาเริ่มต้น
    const sortedSlots = [...timeSlots].sort((a, b) => parseFloat(a.start) - parseFloat(b.start));
    
    const groups = [];
    let currentGroup = [sortedSlots[0]];
    
    for (let i = 1; i < sortedSlots.length; i++) {
        const currentSlot = sortedSlots[i];
        const previousSlot = sortedSlots[i - 1];
        
        // ตรวจสอบว่าช่วงเวลาต่อเนื่องกันหรือไม่
        if (previousSlot.end === currentSlot.start) {
            // ต่อเนื่องกัน เพิ่มเข้ากลุ่มเดิม
            currentGroup.push(currentSlot);
        } else {
            // ไม่ต่อเนื่อง สร้างกลุ่มใหม่
            groups.push(currentGroup);
            currentGroup = [currentSlot];
        }
    }
    
    // เพิ่มกลุ่มสุดท้าย
    groups.push(currentGroup);
    
    return groups;
}

async function initializeBooking() {
    const urlParams = new URLSearchParams(window.location.search);
    fieldId = urlParams.get('field_id');
    
    // ถ้าไม่มี field_id จาก URL ให้ใช้ค่าเริ่มต้นตามประเภทของหน้า
    if (!fieldId) {
        // ดึง field_id ตามประเภทของหน้า (ใหญ่ กลาง เล็ก)
        const pagePath = window.location.pathname;
        if (pagePath.includes('big-reservation')) {
            fieldId = 1; // สำหรับสนามใหญ่
        } else if (pagePath.includes('medium-reservation')) {
            fieldId = 2; // สำหรับสนามกลาง
        } else if (pagePath.includes('small-reservation')) {
            fieldId = 3; // สำหรับสนามเล็ก
        }
    }
    
    if (!fieldId) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/fields/${fieldId}/`);
        if (!response.ok) {
            throw new Error('ไม่สามารถดึงข้อมูลสนามได้');
        }
        
        const field = await response.json();
        
        document.querySelector('h2').textContent = `${field.name} สำหรับ ${field.capacity} คน`;
        pricePerHour = field.price_per_hour;
        
        await checkAvailability();
    } catch (error) {
        console.error('Error:', error);
    }
}

async function checkAvailability() {
    const date = document.getElementById('date').value;
    if (!date) {
        alert('กรุณาเลือกวันที่');
        return;
    }
    
    try {
        // Reset all buttons to default state
        const buttons = document.querySelectorAll('button[data-start]');
        buttons.forEach(button => {
            button.classList.remove('bg-yellow-500', 'bg-red-500');
            button.classList.add('bg-green-500');
            button.disabled = false;
        });
        
        // Fetch availability data
        const response = await fetch(`${API_BASE_URL}/api/check-availability/?date=${date}&field_id=${fieldId}`);
        if (!response.ok) {
            throw new Error('Failed to check availability');
        }
        
        const data = await response.json();
        console.log('Availability data:', data);
        
        // ตรวจสอบว่ามี time_slots หรือไม่
        if (!data.time_slots || !Array.isArray(data.time_slots)) {
            console.error('Invalid time_slots data:', data);
            return;
        }
        
        // สร้าง mapping ของปุ่มทั้งหมด
        const buttonMap = {};
        buttons.forEach(button => {
            const startTime = button.getAttribute('data-start');
            if (startTime) {
                buttonMap[startTime] = button;
            }
        });
        
        // Update button states based on server response
        data.time_slots.forEach(slot => {
            console.log(`Slot: ${slot.start}-${slot.end}, Status: ${slot.status}`);
            
            const button = buttonMap[slot.start];
            if (button) {
                if (slot.status === 'booked') {
                    // สถานะจองแล้ว (สีแดง)
                    button.classList.remove('bg-green-500', 'bg-yellow-500');
                    button.classList.add('bg-red-500');
                    button.disabled = true;
                } else if (slot.status === 'pending') {
                    // สถานะกำลังจอง (สีเหลือง)
                    button.classList.remove('bg-green-500', 'bg-red-500');
                    button.classList.add('bg-yellow-500');
                    button.disabled = true;
                }
            } else {
                console.warn(`Button not found for time slot: ${slot.start} (check your HTML data-start attribute)`);
            }
        });
        
        // Reset selection if current slots are now reserved
        selectedTimes = selectedTimes.filter(time => {
            const button = time.button;
            return !button.classList.contains('bg-red-500') && !button.classList.contains('bg-yellow-500');
        });
        
        // Update display
        updateBookingDisplay();
        
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
        // เรียงลำดับเวลาที่เลือก
        selectedTimes.sort((a, b) => parseFloat(a.start) - parseFloat(b.start));
        
        // แยกเป็นช่วงต่อเนื่อง
        const timeSlotGroups = groupConsecutiveTimeSlots(selectedTimes);
        console.log('Time slot groups:', timeSlotGroups);
        
        // จองทีละช่วงเวลา
        let allBookingsSuccessful = true;
        let bookingPromises = [];
        
        for (const group of timeSlotGroups) {
            const firstTime = group[0];
            const lastTime = group[group.length - 1];
            const totalPrice = group.length * pricePerHour;

            // สร้างข้อมูลสำหรับส่งไปยัง API
            const bookingData = {
                field: parseInt(fieldId),
                reservation_date: date,
                start_time: firstTime.start.replace('.', ':'),
                end_time: lastTime.end.replace('.', ':'),
                customer_name: customerName,
                phone: phone,
                total_price: totalPrice,
                status: 'pending'
            };

            console.log(`Sending booking data for group: ${firstTime.start}-${lastTime.end}`, bookingData);
            
            let csrfToken = '';
            const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfElement) {
                csrfToken = csrfElement.value;
            }

            // สร้าง promise สำหรับการจองแต่ละช่วง
            const bookingPromise = fetch(`${API_BASE_URL}/api/create-reservation/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
                },
                credentials: 'include',
                body: JSON.stringify(bookingData)
            })
            .then(response => response.json())
            .then(result => {
                console.log(`Booking result for ${firstTime.start}-${lastTime.end}:`, result);
                
                if (result.status === 'success') {
                    // เปลี่ยนสีปุ่มที่ถูกจองเป็นสีเหลือง
                    for (let time of group) {
                        const button = time.button;
                        if (button) {
                            button.classList.remove('bg-green-500');
                            button.classList.add('bg-yellow-500');
                            button.disabled = true;
                        }
                    }
                    return true;
                } else {
                    throw new Error(result.message || `ไม่สามารถจองช่วงเวลา ${firstTime.start}-${lastTime.end} ได้`);
                }
            });
            
            bookingPromises.push(bookingPromise);
        }
        
        // รอให้การจองทั้งหมดเสร็จสิ้น
        const results = await Promise.allSettled(bookingPromises);
        
        // ตรวจสอบผลลัพธ์
        const failedBookings = results.filter(result => result.status === 'rejected');
        if (failedBookings.length > 0) {
            const errorMessages = failedBookings.map(result => result.reason.message).join('\n');
            throw new Error(`มีข้อผิดพลาดในการจอง:\n${errorMessages}`);
        }

        // ล้างข้อมูลการจอง
        document.getElementById('reserverName').value = '';
        document.getElementById('reseverPhone').value = '';
        document.getElementById('selectedTimeRange').textContent = '-';
        document.getElementById('totalPrice').textContent = '-';
        document.getElementById('bookingButton').disabled = true;
        
        // ล้าง selectedTimes array
        selectedTimes = [];
        
        // แสดงข้อความสำเร็จ
        alert('ส่งคำขอจองสำเร็จ! กรุณารอการยืนยันจากเจ้าหน้าที่');
        
        // รีเฟรชข้อมูลการจอง
        setTimeout(async () => {
            await checkAvailability();
        }, 1000);

    } catch (error) {
        console.error('Error:', error);
        
        const errorMessage = error.message.includes('ทับซ้อน') 
            ? 'ไม่สามารถจองได้ เนื่องจากช่วงเวลานี้มีการจองแล้ว กรุณาเลือกช่วงเวลาอื่น' 
            : 'เกิดข้อผิดพลาดในการจอง: ' + error.message;
        
        alert(errorMessage);
    }
}