import { useState } from 'react'
import { ArrowRight, CheckCircle } from 'lucide-react'
import { Link } from 'react-router-dom'

// Logo Component
function Logo({ className = 'w-12 h-12' }) {
  return (
    <img 
      src="/assets/custom_fsf/frontend/fsf.png" 
      alt="قوات أمن المنشآت" 
      className={`${className} object-contain`}
    />
  )
}

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess(false)

    try {
      const response = await fetch('/api/method/frappe.core.doctype.user.user.reset_password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          user: email
        })
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess(true)
        setEmail('')
      } else {
        throw new Error(data.message || 'حدث خطأ أثناء إرسال الرابط')
      }
    } catch (err) {
      setError(err.message || 'حدث خطأ، يرجى المحاولة مرة أخرى')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-fsf-primary to-fsf-primary-dark font-arabic">
      {/* Navbar */}
      <nav className="h-[72px] bg-white border-b border-gray-200 shadow-sm">
        <div className="container mx-auto px-4 h-full flex items-center">
          <Link to="/" className="flex items-center gap-3 no-underline">
            <Logo />
            <span className="font-bold text-xl text-fsf-primary">
              قوات أمن المنشآت
            </span>
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-4 relative">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -left-40 w-80 h-80 bg-white/5 rounded-full" />
          <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-white/5 rounded-full" />
        </div>

        {/* Card */}
        <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md p-8 sm:p-10">
          <div className="text-center mb-8">
            <Logo className="w-20 h-20 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-fsf-primary mb-2">
              استعادة كلمة المرور
            </h1>
            <p className="text-fsf-text-muted">
              أدخل بريدك الإلكتروني وسنرسل لك رابطاً لإعادة تعيين كلمة المرور
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg mb-6 text-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6 text-sm flex items-center gap-2">
              <CheckCircle size={20} />
              <span>تم إرسال رابط استعادة كلمة المرور إلى بريدك الإلكتروني</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="mb-6">
              <label 
                htmlFor="email" 
                className="block text-sm font-semibold text-fsf-text mb-2"
              >
                البريد الإلكتروني
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="example@domain.com"
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl bg-gray-50 
                           focus:border-fsf-primary focus:bg-white focus:outline-none 
                           focus:ring-4 focus:ring-fsf-primary/10 transition-all"
                required
                autoFocus
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 bg-fsf-primary text-white rounded-xl font-semibold
                         flex items-center justify-center gap-2
                         hover:bg-fsf-primary-dark transition-all
                         disabled:opacity-70 disabled:cursor-not-allowed
                         hover:-translate-y-0.5 hover:shadow-lg hover:shadow-fsf-primary/30"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>جارٍ الإرسال...</span>
                </>
              ) : (
                <span>إرسال رابط الاستعادة</span>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-200 text-center">
            <Link 
              to="/signin" 
              className="inline-flex items-center gap-2 text-fsf-text-muted text-sm hover:text-fsf-primary transition-colors"
            >
              <ArrowRight size={16} className="rotate-180" />
              العودة لتسجيل الدخول
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-4 text-center text-white/60 text-sm">
        جميع الحقوق محفوظة © {new Date().getFullYear()} قوات أمن المنشآت
      </footer>
    </div>
  )
}


