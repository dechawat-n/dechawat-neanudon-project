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
        const firstTime = selectedTimes[0];
        const lastTime = selectedTimes[selectedTimes.length - 1];
        
        timeRangeElement.textContent = `${firstTime.start} - ${lastTime.end} (${selectedTimes.length} ชั่วโมง)`;
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
    const urlParams = new URLSearchParams(window.location.search);
    fieldId = urlParams.get('field_id');
    
    if (!fieldId) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/fields/?id=${fieldId}`);
        const fieldData = await response.json();
        const field = fieldData[0];
        
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
        
        // Update button states based on server response
        data.time_slots.forEach(slot => {
            const button = document.querySelector(`button[data-start="${slot.start}"]`);
            if (button) {
                if (slot.status === 'reserved') {
                    button.classList.remove('bg-green-500', 'bg-yellow-500');
                    button.classList.add('bg-red-500');
                    button.disabled = true;
                }
            }
        });
        
        // Reset selection if current slots are now reserved
        selectedTimes = selectedTimes.filter(time => {
            const button = time.button;
            return !button.classList.contains('bg-red-500');
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
        const firstTime = selectedTimes[0];
        const lastTime = selectedTimes[selectedTimes.length - 1];
        const totalPrice = selectedTimes.length * pricePerHour;

        const bookingData = {
            field_id: parseInt(fieldId),
            date: date,
            start_time: firstTime.start.replace(':', '.'),
            end_time: lastTime.end.replace(':', '.'),
            customer_name: customerName,
            phone: phone,
            total_price: totalPrice
        };

        console.log('Sending booking data:', bookingData);

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

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

        if (result.status === 'success') {
            // เปลี่ยนสีปุ่มที่ถูกจองเป็นสีแดง
            for (let time of selectedTimes) {
                const button = time.button;
                if (button) {
                    button.classList.remove('bg-yellow-500', 'bg-green-500');
                    button.classList.add('bg-red-500');
                    button.disabled = true;
                }
            }

            // รีเซ็ตฟอร์มและการแสดงผล
            document.getElementById('reserverName').value = '';
            document.getElementById('reseverPhone').value = '';
            document.getElementById('selectedTimeRange').textContent = '-';
            document.getElementById('totalPrice').textContent = '-';
            document.getElementById('bookingButton').disabled = true;

            // ล้าง selectedTimes array หลังจากเปลี่ยนสีปุ่มเสร็จแล้ว
            selectedTimes = [];

            // แสดงข้อความสำเร็จ
            alert('จองสำเร็จ!');
        } else {
            throw new Error(result.message || 'Failed to create reservation');
        }

    } catch (error) {
        console.error('Error:', error);
        alert('เกิดข้อผิดพลาดในการจอง: ' + error.message);
    }
}