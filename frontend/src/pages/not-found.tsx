import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router'
import { Page } from '@/components/page/page'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  return (
    <Page title="Page not found" subtitle="That address doesn't match anything in the prototype.">
      <Button asChild data-enter="action">
        <Link to="/dashboard">
          <ArrowLeft />
          Go to dashboard
        </Link>
      </Button>
    </Page>
  )
}
