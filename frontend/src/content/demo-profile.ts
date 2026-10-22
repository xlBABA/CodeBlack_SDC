// A clearly fictional student used by "Try with a demo student" and "Load demo student".
// No real person, CV or personal data; every field is invented for the demo.
import type { StudentProfile } from '@/types/api'

export const DEMO_PROFILE: StudentProfile = {
  education_level: 'undergraduate',
  degree: 'BSc Data Science',
  semester: 5,
  interests: ['Data analytics', 'Sustainability'],
  skills: [
    { skill_id: 'python', name: 'Python', proficiency: 'intermediate' },
    { skill_id: 'sql', name: 'SQL', proficiency: 'beginner' },
    { skill_id: 'excel', name: 'Excel', proficiency: 'advanced' },
    { skill_id: 'mathematics', name: 'Mathematics', proficiency: 'intermediate' },
    { skill_id: 'critical_thinking', name: 'Critical Thinking', proficiency: 'intermediate' },
  ],
  projects: ['Campus food-waste dashboard (synthetic demo project)', 'Rent price regression notebook (synthetic demo project)'],
  experience_summary: 'Part-time tutor; no professional data experience (fictional demo student).',
}
