import { z } from 'zod'

/** Egyptian mobile: 01xxxxxxxxx */
export const phoneSchema = z
  .string()
  .regex(/^01[0-9]{9}$/, 'Enter a valid Egyptian mobile (01xxxxxxxxx)')

export const loginSchema = z.object({
  phone: phoneSchema,
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

export const registerSchema = loginSchema.extend({
  name: z.string().min(2, 'Name is required'),
})

export const bookingConfirmSchema = z.object({
  players: z.number().int().min(1).max(4),
})

export type LoginValues = z.infer<typeof loginSchema>
export type RegisterValues = z.infer<typeof registerSchema>
export type BookingConfirmValues = z.infer<typeof bookingConfirmSchema>
