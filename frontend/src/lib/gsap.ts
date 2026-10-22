import { gsap } from 'gsap'
import { MotionPathPlugin } from 'gsap/MotionPathPlugin'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'

gsap.registerPlugin(ScrollTrigger, MotionPathPlugin, useGSAP)

export const REDUCED_MOTION = '(prefers-reduced-motion: reduce)'

export { gsap, ScrollTrigger, useGSAP }
