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
    
    // Add resetTimeSlots() when date changes
    dateInput.addEventListener('change', async function() {
        resetTimeSlots(); // Reset selections when date changes
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

    console.log(`selectTimeSlot: ได้รับเวลา ${startTime}-${endTime}`);
    
    const allButtons = document.querySelectorAll('button[data-start]');
    const selectedButtons = Array.from(allButtons).filter(btn => 
        btn.classList.contains('bg-yellow-500') && btn !== button
    );
    
    if (button.classList.contains('bg-green-500')) {
        button.classList.remove('bg-green-500');
        button.classList.add('bg-yellow-500');
        
        const isDuplicate = selectedTimes.some(time => 
            time.start === startTime && time.end === endTime
        );
        
        if (!isDuplicate) {
            selectedTimes.push({
                start: startTime,
                end: endTime,
                button: button
            });
            
            console.log(`เพิ่มช่วงเวลา ${startTime}-${endTime} ในรายการเลือก`);
        }
    } else if (button.classList.contains('bg-yellow-500')) {
        button.classList.remove('bg-yellow-500');
        button.classList.add('bg-green-500');
        
        selectedTimes = selectedTimes.filter(t => !(t.start === startTime && t.end === endTime));
        
        console.log(`ลบช่วงเวลา ${startTime}-${endTime} ออกจากรายการเลือก`);
    }

    updateBookingDisplay();
    
    console.log("เวลาที่เลือกทั้งหมด:", selectedTimes.map(t => `${t.start}-${t.end}`).join(", "));
}

function updateBookingDisplay() {
    const timeRangeElement = document.getElementById('selectedTimeRange');
    const totalPriceElement = document.getElementById('totalPrice');
    const bookingButton = document.getElementById('bookingButton');

    if (selectedTimes.length > 0) {
        selectedTimes.sort((a, b) => {
            const aStart = parseFloat(a.start.replace(':', '.'));
            const bStart = parseFloat(b.start.replace(':', '.'));
            return aStart - bStart;
        });
        
        console.log("เรียงลำดับช่วงเวลาที่เลือก:", selectedTimes.map(t => `${t.start}-${t.end}`).join(", "));

        let timeRanges = [];
        let currentRange = {
            start: selectedTimes[0].start,
            end: selectedTimes[0].end
        };
        
        for (let i = 1; i < selectedTimes.length; i++) {
            const currentTime = parseFloat(selectedTimes[i].start.replace(':', '.'));
            const previousEnd = parseFloat(currentRange.end.replace(':', '.'));
            
            console.log(`ตรวจสอบความต่อเนื่อง: ${currentTime} vs ${previousEnd}`);
            
            if (Math.abs(currentTime - previousEnd) < 0.001) { 
                currentRange.end = selectedTimes[i].end;
                console.log(`ช่วงเวลาต่อเนื่อง ขยายเป็น ${currentRange.start}-${currentRange.end}`);
            } else {

                timeRanges.push({...currentRange}); 
                currentRange = {
                    start: selectedTimes[i].start,
                    end: selectedTimes[i].end
                };
                console.log(`ช่วงเวลาไม่ต่อเนื่อง เริ่มช่วงใหม่ ${currentRange.start}-${currentRange.end}`);
            }
        }
        
        timeRanges.push({...currentRange});
        
        console.log("ช่วงเวลาที่รวมแล้ว:", timeRanges.map(range => `${range.start}-${range.end}`).join(", "));
        
        const timeRangeText = timeRanges.map(range => `${range.start} - ${range.end}`).join(' และ ');
        
        timeRangeElement.textContent = `${timeRangeText} (${selectedTimes.length} ชั่วโมง)`;
        const totalPrice = selectedTimes.length * pricePerHour;
        totalPriceElement.textContent = `${totalPrice.toLocaleString()} บาท`;
        bookingButton.disabled = false;
    } else {
        timeRangeElement.textContent = '-';
        totalPriceElement.textContent = '-';
        bookingButton.disabled = !document.getElementById('reserverName')?.value || 
                                !document.getElementById('reseverPhone')?.value || 
                                document.getElementById('bookingButton').hasAttribute('data-login-required');
    }
}

async function checkAvailability() {
    const date = document.getElementById('date').value;
    if (!date || !fieldId) return;
    
    try {
        const timestamp = new Date().getTime();
        const random = Math.floor(Math.random() * 10000);
        const response = await fetch(`/api/check-availability/?date=${date}&field_id=${fieldId}&t=${timestamp}&r=${random}`);
        
        if (!response.ok) {
            throw new Error('Failed to check availability');
        }
        
        const data = await response.json();
        
        console.log("Time slots from API:", data.time_slots);
        
        const currentButtonStates = {};
        document.querySelectorAll('button[data-start]').forEach(button => {
            const startTime = button.getAttribute('data-start');
            const endTime = button.getAttribute('data-end');
            currentButtonStates[`${startTime}-${endTime}`] = {
                element: button,
                isSelected: selectedTimes.some(t => t.start === startTime && t.end === endTime),
                isDisabled: button.disabled,
                classes: Array.from(button.classList)
            };
        });
        
        const slotStatusMap = {};
        if (data.time_slots) {
            data.time_slots.forEach(slot => {
                let slotStart = slot.start;
                let slotEnd = slot.end === "00.00" ? "24.00" : slot.end;
                slotStatusMap[`${slotStart}-${slotEnd}`] = slot.status;
            });
        }
        
        console.log("Current slot status from API:", slotStatusMap);
        
        const buttons = document.querySelectorAll('button[data-start]');
        buttons.forEach(button => {
            const startTime = button.getAttribute('data-start');
            const endTime = button.getAttribute('data-end');
            const slotKey = `${startTime}-${endTime}`;
            
            const isUserSelected = selectedTimes.some(t => t.start === startTime && t.end === endTime);
            
            button.classList.remove('bg-yellow-500', 'bg-red-500');
            button.classList.add('bg-green-500');
            button.disabled = false;
            
            if (slotStatusMap[slotKey]) {
                const status = slotStatusMap[slotKey];
                
                console.log(`Syncing button ${slotKey} - API status: ${status}, User selected: ${isUserSelected}`);
                
                if (status === 'confirmed') {
                    button.classList.remove('bg-green-500', 'bg-yellow-500');
                    button.classList.add('bg-red-500');
                    button.disabled = true;
                } else if (status === 'pending') {
                    button.classList.remove('bg-green-500', 'bg-red-500');
                    button.classList.add('bg-yellow-500');
                    button.disabled = true;
                }
            }
        });
        
        selectedTimes = selectedTimes.filter(time => {
            const button = document.querySelector(`button[data-start="${time.start}"][data-end="${time.end}"]`);
            return button && !button.disabled;
        });
        
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
    
    const bookingButton = document.getElementById('bookingButton');
    if (bookingButton.disabled) {
        alert('กรุณาเข้าสู่ระบบก่อนทำการจอง');
        return;
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
        const bookedTimes = [...selectedTimes].map(t => ({...t}));
        console.log("ช่วงเวลาที่ต้องการจอง:", bookedTimes.map(t => `${t.start}-${t.end}`).join(", "));
        
        const sortedTimes = [...selectedTimes].sort((a, b) => {
            const aStart = parseFloat(a.start.replace(':', '.'));
            const bStart = parseFloat(b.start.replace(':', '.'));
            return aStart - bStart;
        });
        
        let consecutiveGroups = [];
        if (sortedTimes.length > 0) {
            let currentGroup = [sortedTimes[0]];
            
            for (let i = 1; i < sortedTimes.length; i++) {
                const currentSlot = sortedTimes[i];
                const lastSlotInGroup = currentGroup[currentGroup.length - 1];
                
                const currentStart = parseFloat(currentSlot.start.replace(':', '.'));
                const lastEnd = parseFloat(lastSlotInGroup.end.replace(':', '.'));
                
                console.log(`Comparing: Current start ${currentStart} vs Last end ${lastEnd}`);
                
                if (Math.abs(currentStart - lastEnd) < 0.01) { 
                    currentGroup.push(currentSlot);
                } else {
                    consecutiveGroups.push([...currentGroup]);
                    currentGroup = [currentSlot];
                }
            }
            
            consecutiveGroups.push([...currentGroup]);
        }
        
        console.log("กลุ่มเวลาที่จะจอง:", 
            consecutiveGroups.map(group => 
                `${group[0].start}-${group[group.length-1].end}`
            ).join(", ")
        );
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        let failedBookings = [];
        let successfulBookings = [];
        
        let successfulSlots = [];
        
        for (const group of consecutiveGroups) {
            const startTime = group[0].start;
            let endTime = group[group.length - 1].end;
            
            const apiEndTime = endTime === '24.00' ? '00.00' : endTime;
            
            const groupHours = group.length;
            
            console.log(`กำลังจอง: ${startTime}-${endTime}, ${groupHours} ชั่วโมง`);

            const bookingData = {
                field_id: parseInt(fieldId),
                date: date,
                start_time: startTime.replace(':', '.'),
                end_time: apiEndTime.replace(':', '.'),
                customer_name: customerName,
                phone: phone,
                total_price: pricePerHour * groupHours,
                time_slots: group.map(slot => {
                    let apiSlotEnd = slot.end === '24.00' ? '00.00' : slot.end;
                    return { 
                        start: slot.start, 
                        end: apiSlotEnd 
                    };
                })
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
                
                if (!response.ok) {
                    if (response.status === 401) {
                        alert('กรุณาเข้าสู่ระบบก่อนทำการจอง');
                        window.location.href = '/login/';
                        return;
                    }
                    
                    const result = await response.json();
                    throw new Error(result.message || 'การจองไม่สำเร็จ');
                }
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    console.log(`จองสำเร็จสำหรับ ${startTime}-${endTime}`);
                    successfulBookings.push(`${startTime}-${endTime}`);
                    
                    group.forEach(slot => {
                        successfulSlots.push({
                            start: slot.start,
                            end: slot.end
                        });
                    });
                } else {
                    throw new Error(result.message || 'การจองไม่สำเร็จ');
                }
            } catch (error) {
                console.error(`เกิดข้อผิดพลาดในการจอง ${startTime}-${endTime}:`, error);
                failedBookings.push({
                    timeSlot: `${startTime}-${endTime}`,
                    reason: error.message
                });
            }
        }
        
        if (failedBookings.length > 0) {
            const errorMessage = failedBookings.map(booking => 
                `เวลา ${booking.timeSlot}: ${booking.reason}`
            ).join('\n');
            
            alert(`มีบางช่วงเวลาที่จองไม่สำเร็จ:\n${errorMessage}`);
        } else {
            alert('จองสำเร็จ! รอการยืนยันจากผู้ดูแลระบบ');
        }
        
        document.getElementById('reserverName').value = '';
        document.getElementById('reseverPhone').value = '';
        
        if (successfulBookings.length > 0) {
            console.log("จองสำเร็จแล้วสำหรับช่วงเวลา:", successfulBookings.join(", "));
        }
        
        if (successfulSlots.length > 0) {
            const buttons = document.querySelectorAll('button[data-start]');
            buttons.forEach(button => {
                const startTime = button.getAttribute('data-start');
                const endTime = button.getAttribute('data-end');
                
                const isBooked = successfulSlots.some(slot => 
                    slot.start === startTime && slot.end === endTime
                );
                
                if (isBooked) {
                    button.classList.remove('bg-green-500', 'bg-red-500');
                    button.classList.add('bg-yellow-500');
                    button.disabled = true;
                }
            });
        }
        
        selectedTimes = [];
        updateBookingDisplay();
        setTimeout(async () => {
            await checkAvailability();
        }, 500);
        
    } catch (error) {
        console.error('Error:', error);
        alert('เกิดข้อผิดพลาดในการจอง: ' + error.message);
    }
}