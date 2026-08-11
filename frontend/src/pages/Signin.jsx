import { useState } from 'react'

const heroImage = '/assets/custom_fsf/frontend/login-hero.png'
const logoImage = '/assets/custom_fsf/frontend/fsf.png'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [lang, setLang] = useState('en')

  const isArabic = lang === 'ar'
  const t = {
    brand: isArabic ? 'نظام إدارة التقنية والذكاء الاصطناعي' : 'Tech & AI Management System',
    username: isArabic ? 'اسم المستخدم' : 'Username',
    password: isArabic ? 'كلمة المرور' : 'Password',
    login: isArabic ? 'تسجيل الدخول' : 'Login',
    loading: isArabic ? 'جاري تسجيل الدخول...' : 'Logging in...',
    badCreds: isArabic ? 'اسم المستخدم أو كلمة المرور غير صحيحة' : 'Username or password is incorrect',
    failed: isArabic ? 'فشل تسجيل الدخول' : 'Failed to login',
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch('/api/method/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          usr: username,
          pwd: password,
        })
      })

      const data = await response.json()
      if (response.ok && data.message === 'Logged In') {
        const params = new URLSearchParams(window.location.search)
        const redirectTo = sessionStorage.getItem('redirect-to') || params.get('redirect-to') || '/app'
        sessionStorage.removeItem('redirect-to')
        window.location.href = redirectTo
      } else {
        throw new Error(data.message || t.failed)
      }
    } catch (err) {
      setError(err.message || t.badCreds)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-screen overflow-hidden bg-white" dir={isArabic ? 'rtl' : 'ltr'}>
      <div className="grid h-screen grid-cols-1 lg:grid-cols-2">
        <div className="relative flex h-screen flex-col bg-white shadow-[5px_0_28.5px_rgba(0,0,0,0.09)]">
          <header className="flex items-center justify-between px-6 py-5 sm:px-10">
            <a href="/">
              <img
                src={logoImage}
                alt="FSF logo"
                className="h-[55px] w-[48px] object-contain"
              />
            </a>
            <button
              type="button"
              onClick={() => {
                setLang(isArabic ? 'en' : 'ar')
                setError('')
              }}
              className="text-[16px] text-[#252525] transition-opacity hover:opacity-75"
              aria-label="Change language"
            >
              {isArabic ? 'English' : 'عربي'}
            </button>
          </header>

          <main className="flex flex-1 items-center px-6 sm:px-10 lg:px-[84px]">
            <div className="w-full max-w-[420px]">
              <div className="mb-8">
                <p className="text-[16px] font-medium leading-6 text-[#1b8354]">
                  {isArabic ? 'قوات أمن المنشآت' : 'Facilities Security Force'}
                </p>
                <h1 className="mt-1 text-[40px] font-medium leading-[1.18] tracking-[-0.72px] text-black sm:text-[48px]">
                  {t.brand}
                </h1>
              </div>

              <form className="w-full" onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <input
                    type="text"
                    name="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder={t.username}
                    autoComplete="username"
                    className="h-[48px] w-full rounded-[8px] border border-[#e4eaf1] px-4 text-[16px] text-black outline-none transition-colors placeholder:text-[#919191] focus:border-[#1b8354]"
                    required
                  />
                  <input
                    type="password"
                    name="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={t.password}
                    autoComplete="current-password"
                    className="h-[48px] w-full rounded-[8px] border border-[#e4eaf1] px-4 text-[16px] text-black outline-none transition-colors placeholder:text-[#919191] focus:border-[#1b8354]"
                    required
                  />
                </div>

                {error && (
                  <p className="mt-3 rounded-[8px] border border-red-200 bg-red-50 px-3 py-2 text-[14px] text-red-700">
                    {error}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="mt-4 h-[48px] w-full rounded-[8px] bg-[#1b8354] text-[16px] font-bold text-white transition-colors hover:bg-[#166b45] active:bg-[#125a3b] disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {loading ? t.loading : t.login}
                </button>
              </form>
            </div>
          </main>
        </div>

        <div className="hidden h-screen overflow-hidden lg:block">
          <img
            src={heroImage}
            alt="Login illustration"
            className="h-full w-full object-cover object-top"
          />
        </div>
      </div>
    </div>
  )
}
