import { staffPassSchedule } from './staff-pass.ts'

function check(cond: unknown, msg: string) {
  if (!cond) throw new Error(msg)
}

const flat = staffPassSchedule({
  court: { name: 'Court 1' },
  date: '2026-08-20',
  start_time: '18:00',
  end_time: '20:00',
})
check(flat?.date === '2026-08-20', 'flat date')
check(flat?.startTime === '18:00', 'flat start')
check(flat?.endTime === '20:00', 'flat end')

const fromSlots = staffPassSchedule({
  slots: [
    {
      court: { name: 'Court 2' },
      date: '2026-08-21',
      start_time: '18:00',
      end_time: '19:00',
    },
    {
      date: '2026-08-21',
      start_time: '19:00',
      end_time: '20:00',
    },
  ],
})
check(fromSlots?.courtName === 'Court 2', 'slots court')
check(fromSlots?.date === '2026-08-21', 'slots date')
check(fromSlots?.startTime === '18:00', 'slots start')
check(fromSlots?.endTime === '20:00', 'slots end')

check(staffPassSchedule({ slots: [] }) === null, 'empty slots')
check(staffPassSchedule({}) === null, 'missing schedule')

console.log('staff-pass check ok')
