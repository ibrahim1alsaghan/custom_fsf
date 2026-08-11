import React, { useState, useEffect, useRef } from 'react'
import { LogIn, Menu, X, Info, Search, Globe, ChevronLeft, ChevronRight, FileText, Calendar, ArrowLeft, Shield, MapPin, Youtube, Twitter } from 'lucide-react'
import { Link } from 'react-router-dom'

// =============================================================================
// STYLES & CONFIG
// =============================================================================
const THEME = {
  primary: '#1A3C34',    
  accent: '#10B981',     
  button: '#198754',     
  bgLight: '#F8F9FA',    
  textMain: '#1F2937',
  textSub: '#6B7280'
}

const API_BASE = '/api/method'
const ENDPOINTS = {
  ALERTS: 'custom_fsf.www.landing.get_alerts',
  NEWS: 'custom_fsf.www.landing.get_news',
  EVENTS: 'custom_fsf.www.landing.get_events'
}

const TEXTS = {
  ar: {
    dir: 'rtl',
    lang: 'ar',
    nav: {
      login: 'تسجيل الدخول',
      home: 'الرئيسية',
      services: 'الخدمات',
      alerts: 'التنبيهات',
      news: 'الأخبار',
      events: 'الأحداث و الفعاليات',
      contact: 'تواصل معنا',
      langToggle: 'En'
    },
    hero: {
      title: 'إدارة الأمن السيبراني',
      desc: 'هنا يمكنك إضافة وصف مختصر حول الغرض من البوابة متبوعًا بزر الحث على اتخاذ إجراء وصورة أو رسم توضيحي على الجانب الأيسر.'
    },
    alerts: {
      title: 'التنبيهات',
      desc: 'هنا يمكنك إضافة وصف مختصر حول الغرض من البوابة متبوعًا بزر الحث على اتخاذ إجراء.',
      severity: 'مستوى الخطورة',
      date: 'تاريخ التحذير',
      target: 'القطاع المستهدف',
      general: 'عام',
      details: 'عرض التفاصيل',
      more: 'عرض المزيد',
      levels: {
        'CRITICAL': 'عالٍ جداً',
        'HIGH': 'عالي',
        'MEDIUM': 'متوسط',
        'LOW': 'منخفض'
      }
    },
    news: {
      title: 'الأخبار',
      desc: 'حيث كل خبر يحمل قصة، وكل حدث يصنع فرقاً.',
      more: 'عرض المزيد'
    },
    services: {
      title: 'الخدمات الإلكترونية',
      desc: 'هنا يمكنك إضافة وصف مختصر حول الغرض من البوابة.',
      details: 'عرض التفاصيل',
      more: 'عرض المزيد',
      updated: 'تاريخ آخر تعديل: 7/10/2025 - 4:13 م'
    },
    events: {
      title: 'الأحداث و الفعاليات',
      details: 'تفاصيل الحدث',
      status: 'فاعلية',
      more: 'عرض المزيد'
    },
    links: {
      title: 'روابط هامة',
      desc: 'أهم الروابط المقترحة من البوابة',
      more: 'عرض المزيد',
      logo: 'شعار البوابة'
    },
    footer: {
      overview: 'نظرة عامة',
      about: 'حول قوات أمن المنشآت',
      privacy: 'الخصوصية وشروط الاستخدام',
      news: 'الأخبار والأحداث',
      contact: 'الاتصال والدعم',
      connect: 'تواصل معنا',
      share: 'شارك معنا',
      media: 'المركز الإعلامي',
      innovation: 'الابتكار',
      follow: 'تابعنا على',
      map: 'خريطة الموقع',
      sla: 'اتفاقية مستوى الخدمة',
      rules: 'اللوائح والتعليمات',
      rights: 'جميع الحقوق محفوظة لقوات أمن المنشآت © 2025',
      developed: 'تم تطويره وصيانته بواسطة قوات أمن المنشآت',
      updated: 'تاريخ آخر تعديل: 10/12/2025'
    }
  },
  en: {
    dir: 'ltr',
    lang: 'en',
    nav: {
      login: 'Login',
      home: 'Home',
      services: 'Services',
      alerts: 'Alerts',
      news: 'News',
      events: 'Events & Activities',
      contact: 'Contact Us',
      langToggle: 'عربي'
    },
    hero: {
      title: 'Cybersecurity Management',
      desc: 'Here you can add a brief description about the purpose of the portal followed by a call to action button and an illustration on the side.'
    },
    alerts: {
      title: 'Alerts',
      desc: 'Here you can add a brief description about the purpose of the portal followed by a call to action.',
      severity: 'Severity',
      date: 'Warning Date',
      target: 'Target Sector',
      general: 'General',
      details: 'View Details',
      more: 'View More',
      levels: {
        'Critical': 'Critical',
        'High': 'High',
        'Medium': 'Medium',
        'Low': 'Low'
      }
    },
    news: {
      title: 'News',
      desc: 'Where every news carries a story, and every event makes a difference.',
      more: 'View More'
    },
    services: {
      title: 'E-Services',
      desc: 'Here you can add a brief description about the purpose of the portal.',
      details: 'View Details',
      more: 'View More',
      updated: 'Last updated: 7/10/2025 - 4:13 PM'
    },
    events: {
      title: 'Events & Activities',
      details: 'Event Details',
      status: 'Event',
      more: 'View More'
    },
    links: {
      title: 'Important Links',
      desc: 'Most important suggested links from the portal',
      more: 'View All',
      logo: 'Portal Logo'
    },
    footer: {
      overview: 'Overview',
      about: 'About FSF',
      privacy: 'Privacy & Terms',
      news: 'News & Events',
      contact: 'Contact & Support',
      connect: 'Contact Us',
      share: 'Participate',
      media: 'Media Center',
      innovation: 'Innovation',
      follow: 'Follow Us',
      map: 'Sitemap',
      sla: 'SLA',
      rules: 'Regulations',
      rights: 'All rights reserved to Facilities Security Forces © 2025',
      developed: 'Developed and maintained by Facilities Security Forces',
      updated: 'Last updated: 10/12/2025'
    }
  }
}

// Mock data needs to be language agnostic or translated on backend. 
// For static mock data, we can define translations.
const SERVICES_DATA = [
  { 
    id: 1, 
    title: { ar: 'طلب اجتماع عن بعد عبر التيمز', en: 'Request a Remote Teams Meeting' }, 
    subtitle: { ar: 'خدمة تتيح للمستفيد تقديم طلب لعقد اجتماع عن بُعد عبر منصة Microsoft Teams، مع تحديد الموضوع والأطراف المعنية وموعد الاجتماع.', en: 'Submit a request to schedule an online meeting via Microsoft Teams, including topic, stakeholders, and preferred time.' }, 
    icon: FileText ,
    url: '/login'
  },
  { 
    id: 2, 
    title: { ar: 'طلب صلاحية وصول لنظام', en: 'Request System Access Permission' }, 
    subtitle: { ar: 'خدمة تتيح للمستخدم التقدم بطلب للحصول على صلاحية الدخول لنظام معين وفق السياسات المعتمدة.', en: 'Apply for access permissions to a specific system in line with approved policies.' }, 
    icon: FileText ,
    url: '/login'
  },
  { 
    id: 3, 
    title: { ar: 'طلب صلاحية الدعم الفني Hdesk', en: 'Request Help Desk Support Permission' }, 
    subtitle: { ar: 'خدمة تُمكّن المستفيد من طلب صلاحية الدعم الفني (Help Desk) على الأنظمة بما يضمن تمكين فرق الدعم من أداء المهام وفق الصلاحيات المعتمدة.', en: 'Request Help Desk support permissions on systems to enable support teams to operate within approved privileges.' },
    icon: FileText ,
    url: '/login'
  },
  { 
    id: 4, 
    title: { ar: 'طلب خدمة فتح منافذ على الشبكة', en: 'Request Network Port Opening Service' }, 
    subtitle: { ar: 'خدمة تتيح للمستفيد من طلب فتح منافذ محددة على الشبكة لتمكين الاتصال الآمن بين الأنظمة.', en: 'Request opening specific network ports to enable secure connectivity between systems.' }, 
    icon: FileText ,
    url: '/login'
  },
]

const IMPORTANT_LINKS = [
  { id: 1, image: '/assets/custom_fsf/frontend/moi.png', url: 'https://www.moi.gov.sa/' },
  { id: 2, image: '/assets/custom_fsf/frontend/fg.png', url: 'https://www.fg.gov.sa/' },
  { id: 3, image: '/assets/custom_fsf/frontend/998.png', url: 'https://www.998.gov.sa/' },
  { id: 4, image: '/assets/custom_fsf/frontend/passport.png', url: 'https://www.moi.gov.sa/wps/vanityurl/ar/passports' },
  { id: 5, image: '/assets/custom_fsf/frontend/civil.png', url: 'https://www.moi.gov.sa/wps/vanityurl/ar/civilaffairs' },
  { id: 6, image: '/assets/custom_fsf/frontend/sfh.png', url: 'https://www.sfh.med.sa/' },
  { id: 7, image: '/assets/custom_fsf/frontend/interior.png', url: 'https://interior.moi.gov.sa/' },
  { id: 8, image: '/assets/custom_fsf/frontend/nvg.png', url: 'https://nvg.gov.sa/' },
  { id: 9, image: '/assets/custom_fsf/frontend/efaa.png', url: 'https://efaa.sa/' },
]

// Calendar component for events - Compact version
function EventCalendar({ events = [], lang = 'ar' }) {
  const now = new Date()
  const isRTL = lang === 'ar'

  // State for currently displayed month/year
  const [displayMonth, setDisplayMonth] = useState(now.getMonth())
  const [displayYear, setDisplayYear] = useState(now.getFullYear())

  // Get month name
  const monthNames = {
    ar: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'],
    en: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
  }

  // Day names: Arabic week starts Saturday, English week starts Sunday
  const dayNames = {
    ar: ['س', 'ح', 'ن', 'ث', 'ر', 'خ', 'ج'], // Saturday, Sunday, Monday, Tuesday, Wednesday, Thursday, Friday
    en: ['S', 'M', 'T', 'W', 'T', 'F', 'S']  // Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday
  }

  // Navigation functions
  const goToPreviousMonth = () => {
    if (displayMonth === 0) {
      setDisplayMonth(11)
      setDisplayYear(displayYear - 1)
    } else {
      setDisplayMonth(displayMonth - 1)
    }
  }

  const goToNextMonth = () => {
    if (displayMonth === 11) {
      setDisplayMonth(0)
      setDisplayYear(displayYear + 1)
    } else {
      setDisplayMonth(displayMonth + 1)
    }
  }

  const goToToday = () => {
    setDisplayMonth(now.getMonth())
    setDisplayYear(now.getFullYear())
  }

  // Check if displayed month is current month
  const isCurrentMonth = displayMonth === now.getMonth() && displayYear === now.getFullYear()

  // Parse event dates and create a set of days with events for the displayed month
  const eventDays = new Set()
  events.forEach(event => {
    if (event.dateGreg) {
      try {
        const eventDate = new Date(event.dateGreg)
        if (eventDate.getMonth() === displayMonth && eventDate.getFullYear() === displayYear) {
          eventDays.add(eventDate.getDate())
        }
      } catch (e) {
        // Ignore invalid dates
      }
    }
  })

  // Get first day of month and number of days
  const firstDay = new Date(displayYear, displayMonth, 1)
  const lastDay = new Date(displayYear, displayMonth + 1, 0)
  const daysInMonth = lastDay.getDate()
  const startingDayOfWeek = firstDay.getDay() // 0 = Sunday, 1 = Monday, ..., 6 = Saturday

  // Adjust starting position based on language
  // Arabic: week starts on Saturday (6), so Sunday (0) should be in position 1
  // English: week starts on Sunday (0), so Sunday should be in position 0
  const adjustedStartingDay = isRTL
    ? (startingDayOfWeek + 1) % 7  // Shift by 1 for Arabic (Saturday = 0)
    : startingDayOfWeek              // No shift for English (Sunday = 0)

  // Create calendar grid
  const calendarDays = []

  // Add empty cells for days before month starts
  for (let i = 0; i < adjustedStartingDay; i++) {
    calendarDays.push(null)
  }

  // Add days of the month
  for (let day = 1; day <= daysInMonth; day++) {
    calendarDays.push(day)
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm p-5 max-w-[320px] w-full ${isRTL ? 'text-right' : 'text-left'}`}>
      <div className="mb-3">
        {/* Month navigation header */}
        <div className="flex items-center justify-between mb-1">
          <button
            onClick={goToPreviousMonth}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            aria-label={isRTL ? 'الشهر السابق' : 'Previous month'}
          >
            {isRTL ? <ChevronRight size={16} className="text-gray-600" /> : <ChevronLeft size={16} className="text-gray-600" />}
          </button>

          <div className="flex-1 text-center">
            <h3 className="text-sm font-bold text-gray-800">
              {monthNames[lang][displayMonth]} {displayYear}
            </h3>
          </div>

          <button
            onClick={goToNextMonth}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            aria-label={isRTL ? 'الشهر التالي' : 'Next month'}
          >
            {isRTL ? <ChevronLeft size={16} className="text-gray-600" /> : <ChevronRight size={16} className="text-gray-600" />}
          </button>
        </div>

        {/* Today button */}
        {!isCurrentMonth && (
          <button
            onClick={goToToday}
            className="text-[10px] text-[#198754] hover:text-[#146c43] font-medium"
          >
            {isRTL ? 'العودة للشهر الحالي' : 'Go to current month'}
          </button>
        )}
      </div>

      {/* Day headers */}
      <div className="grid grid-cols-7 gap-0.5 mb-1">
        {dayNames[lang].map((day, idx) => (
          <div key={idx} className="text-center text-[10px] font-semibold text-gray-500 py-1">
            {day}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-0.5">
        {calendarDays.map((day, idx) => {
          const isToday = isCurrentMonth && day === now.getDate() && displayYear === now.getFullYear()
          const hasEvent = day && eventDays.has(day)

          return (
            <div
              key={idx}
              className={`
                w-9 h-9 flex items-center justify-center text-xs font-medium rounded
                ${day === null ? 'bg-transparent' : ''}
                ${day && !isToday && !hasEvent ? 'text-gray-600 hover:bg-gray-50' : ''}
                ${isToday && !hasEvent ? 'bg-[#198754] text-white font-bold' : ''}
                ${hasEvent && !isToday ? 'bg-orange-100 text-orange-700 font-bold border border-orange-300' : ''}
                ${hasEvent && isToday ? 'bg-[#198754] text-white font-bold border border-orange-300' : ''}
                transition-colors
              `}
              title={hasEvent ? `${day} ${monthNames[lang][displayMonth]} - ${events.filter(e => {
                try {
                  const d = new Date(e.dateGreg)
                  return d.getDate() === day && d.getMonth() === displayMonth && d.getFullYear() === displayYear
                } catch { return false }
              }).length} ${isRTL ? 'حدث' : 'event(s)'}` : ''}
            >
              {day}
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className={`mt-3 pt-3 border-t border-gray-200 flex flex-wrap gap-3 text-[10px] ${isRTL ? 'justify-end' : 'justify-start'}`}>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-[#198754]"></div>
          <span className="text-gray-600">{isRTL ? 'اليوم' : 'Today'}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-orange-100 border border-orange-300"></div>
          <span className="text-gray-600">{isRTL ? 'أحداث' : 'Events'}</span>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

const SectionHeader = ({ title, icon: Icon, t , moreHref}) => (
  <div className="flex items-center gap-4 mb-8">
    {/* Green bar */}
    <div className="h-8 w-1 bg-[#198754] rounded-full shrink-0"></div>
    {/* Title + icon */}
    <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2 shrink-0">
      {title}
      {Icon && <Icon size={24} className="text-gray-400" />}
    </h2>
    {/* Thick line */}
    <div className="flex-1 border-t-2 border-gray-200"></div>
    {/* Action button */}
    <a
      href={moreHref || '#'}
      className="px-4 py-2 border border-gray-200 text-gray-600 rounded hover:bg-gray-50 text-sm font-medium transition-colors shrink-0"
    >
      {t.more}
    </a>
  </div>
)

const Logo = ({ className = "h-12 w-auto" }) => (
    <img src="/assets/custom_fsf/frontend/fsf.png" alt="FSF Logo" className={className} />
)

function Navbar({ currentLang, toggleLang, t }) {
  const [isOpen, setIsOpen] = useState(false)
  const isRTL = t?.dir === 'rtl'

  // In RTL mode, "flex-row" means items flow from Right to Left.
  // We want Logo on Right (Start) and Menu on Left (End) in RTL.
  // In LTR mode, "flex-row" means items flow from Left to Right.
  // We want Logo on Left (Start) and Menu on Right (End) in LTR.
  // The structure below achieves this naturally with 'justify-between' if Logo group is first.
  
  return (
    <nav className="sticky top-0 bg-white border-b border-gray-200 z-50">
      <div className="container mx-auto px-4 h-[80px] flex items-center justify-between">
        
        {/* Group 1: Logo & Links (Start - Right in RTL, Left in LTR) */}
        <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center">
                <Logo />
            </Link>
            <div className="hidden lg:flex items-center gap-6 text-sm font-medium text-gray-600">
                <a href="#" className="text-[#1A3C34] font-bold">{t.nav.home}</a>
                <a href="#alerts" className="hover:text-[#1A3C34]">{t.nav.alerts}</a>
                <a href="#news" className="hover:text-[#1A3C34]">{t.nav.news}</a>
                <a href="#services" className="hover:text-[#1A3C34]">{t.nav.services}</a>
                <a href="#events" className="hover:text-[#1A3C34]">{t.nav.events}</a>
                <a href="#links" className="hover:text-[#1A3C34]">{t.nav.contact}</a>
            </div>
        </div>

        {/* Group 2: Actions (End - Left in RTL, Right in LTR) */}
        <div className="flex items-center gap-4">
          <button className="p-2 text-gray-500 hover:text-[#1A3C34]">
             <Search size={20} />
          </button>
          <span className="text-gray-300">|</span>
          <span 
            className="text-sm font-medium cursor-pointer hover:text-[#1A3C34]" 
            onClick={toggleLang}
          >
            {t.nav.langToggle}
          </span>
          <Link to="/signin" className="flex items-center gap-2 text-gray-700 hover:text-[#1A3C34] font-medium border-s border-gray-200 pl-4 ms-2">
             <LogIn size={20} />
             <span>{t.nav.login}</span>
          </Link>
          
          <button className="lg:hidden p-2" onClick={() => setIsOpen(!isOpen)}>
              <Menu />
          </button>
        </div>
      </div>
    </nav>
  )
}

function Hero({ t }) {
  return (
    <section className="relative h-[600px] bg-[#1A3C34] overflow-hidden">
      <div className="absolute inset-0">
        <img 
          src="/assets/custom_fsf/frontend/Hero.png" 
          alt="Control Room" 
          className="w-full h-full object-cover opacity-60 mix-blend-overlay"
        />
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#1A3C34]/80 to-transparent"></div>
      </div>
      
      <div className="container mx-auto px-4 relative z-10 h-full flex flex-col justify-center items-start">
        <h1 className="text-5xl font-bold text-white mb-6">{t.hero.title}</h1>
        <p className="text-gray-200 text-lg max-w-xl mb-12 leading-relaxed">
          {t.hero.desc}
        </p>
        
      </div>
    </section>
  )
}

function AlertsSection({ alerts, t, lang }) {
  if (!alerts || alerts.length === 0) return null
  const isRTL = t?.dir === 'rtl'

  return (
    <section id="alerts" className="py-16 bg-white">
      <div className="container mx-auto px-4">
        <SectionHeader title={t.alerts.title} icon={Info} t={t.alerts} moreHref="https://nca.gov.sa/ar/cert/" />
        <p className="text-gray-500 mb-8 -mt-4 text-sm">{t.alerts.desc}</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {alerts.map((alert, idx) => {
            // Get language-specific values
            const title = typeof alert.title === 'object' ? (alert.title[lang] || alert.title.en || alert.title.ar || '') : alert.title
            const sectors = typeof alert.sectors === 'object' ? (alert.sectors[lang] || alert.sectors.en || alert.sectors.ar || []) : (alert.sectors || [])

            return (
              <div
                key={idx}
                className={`bg-white border border-gray-100 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow ${isRTL ? 'text-right' : 'text-left'}`}
              >
                {alert.iconUrl && (
                  <div className="flex justify-center mb-4">
                    <img src={alert.iconUrl} alt="" className="h-12 w-12 object-contain" />
                  </div>
                )}
                <h3 className="text-center font-bold text-gray-800 text-base mb-5">{title}</h3>

                <div className="space-y-3 mb-5">
                   {/* Severity row */}
                   <div className="flex justify-between items-center">
                      <span className="font-semibold text-gray-700 text-sm">{t.alerts.severity}</span>
                      <span className="bg-orange-100 text-orange-600 px-2 py-0.5 rounded text-xs font-semibold">
                        {t.alerts.levels[alert.severity] || alert.severity}
                      </span>
                   </div>

                   {/* Date row */}
                   <div className="flex justify-between items-center">
                      <span className="font-semibold text-gray-700 text-sm">{t.alerts.date}</span>
                      <span className="text-gray-500 text-sm">{alert.date}</span>
                   </div>

                   {/* Target sector */}
                   <div className="space-y-2">
                      <div className="font-semibold text-gray-700 text-sm">{t.alerts.target}</div>
                      <div className={`flex flex-wrap gap-1.5 ${isRTL ? 'justify-end' : 'justify-start'}`}>
                        {sectors && sectors.length > 0 ? (() => {
                          const visible = sectors.slice(0, 2)
                          const remaining = sectors.length - visible.length
                          return (
                            <>
                              {visible.map((s, i) => (
                                <span key={i} className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs">
                                  {s}
                                </span>
                              ))}
                              {remaining > 0 && (
                                <span className="bg-gray-200 text-gray-700 px-2 py-0.5 rounded text-xs">
                                  +{remaining}
                                </span>
                              )}
                            </>
                          )
                        })() : (
                          <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs">{t.alerts.general}</span>
                        )}
                      </div>
                   </div>
                </div>

                <div className="flex justify-start">
                  <a
                    href={alert.url || '#'}
                    target={alert.url ? '_blank' : '_self'}
                    rel="noopener noreferrer"
                    className="inline-block bg-[#198754] text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-[#146c43] transition-colors"
                  >
                    {t.alerts.details}
                  </a>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

function NewsSection({ news, t }) {
  if (!news || news.length === 0) return null

  const [activeIdx, setActiveIdx] = useState(0)
  const featured = news[activeIdx] || news[0]

  // Limit standard news to exactly 2 items
  const standard = news.filter((_, idx) => idx !== activeIdx).slice(0, 2)
  
  const isRTL = t?.dir === 'rtl'

  const prev = () => setActiveIdx((prevIdx) => (prevIdx === 0 ? news.length - 1 : prevIdx - 1))
  const next = () => setActiveIdx((prevIdx) => (prevIdx === news.length - 1 ? 0 : prevIdx + 1))

  return (
      <section id="news" className="py-16 bg-[#F8F9FA]">
          <div className="container mx-auto px-4">
              <SectionHeader title={t.news.title} icon={FileText} t={t.news} moreHref="https://www.fsf.gov.sa/media-center/forces-news" />
              <p className="text-gray-500 mb-8 -mt-4 text-sm">{t.news.desc}</p>

              {/* MAIN GRID: Changed to 4 columns to allow for 50%/25%/25% split */}
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  
                  {/* STANDARD NEWS (The 2 smaller ones)
                      - lg:col-span-2: Takes 50% of total width (2 out of 4 cols)
                      - lg:order-2: Puts them on the Left side in RTL (End)
                      - grid-cols-2: Splits this container in half again (25% each item)
                  */}
                  <div className="lg:col-span-2 lg:order-2 grid grid-cols-1 sm:grid-cols-2 gap-6 h-[500px]">
                      {standard.map(item => (
                          <div key={item.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm flex flex-col h-full">
                              <div className="h-48">
                                  <img src={item.image} alt={item.title} className="w-full h-full object-cover" />
                              </div>
                              <div className="p-5 flex flex-col flex-grow">
                                  <h3 className="font-bold text-gray-800 mb-3 leading-snug line-clamp-2">{item.title}</h3>
                                  <p className="text-xs text-gray-500 mb-4 line-clamp-3 leading-relaxed flex-grow">{item.desc}</p>
                                  <div className="flex justify-start mt-auto">
                                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="inline-block bg-[#198754] text-white px-5 py-1.5 rounded text-sm font-medium hover:bg-[#146c43] transition-colors">
                                        {t.news.more}
                                    </a>
                                  </div>
                              </div>
                          </div>
                      ))}
                  </div>

                  {/* FEATURED NEWS (The big one)
                      - lg:col-span-2: Takes 50% of total width (2 out of 4 cols)
                      - lg:order-1: Puts it on the Right side in RTL (Start)
                  */}
                  {featured && (
                      <div className="lg:col-span-2 lg:order-1 relative group rounded-2xl overflow-hidden h-[500px]">
                           <a href={featured.url || '#'} target={featured.url ? '_blank' : '_self'} rel="noopener noreferrer" className="block h-full">
                             <img src={featured.image} alt={featured.title} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
                             <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex flex-col justify-end p-8 text-white">
                                <h3 className="text-2xl font-bold mb-4 leading-normal">{featured.title}</h3>
                                <p className="text-gray-200 mb-6 text-sm leading-relaxed line-clamp-3">{featured.desc}</p>
                             </div>
                           </a>
                           {/* Controls */}
                           <div className="absolute inset-0 flex items-center justify-between px-4 pointer-events-none">
                             <button onClick={prev} className="w-10 h-10 rounded-full bg-black/40 text-white flex items-center justify-center hover:bg-black/60 transition pointer-events-auto">
                               {isRTL ? <ChevronRight size={18} /> : <ChevronRight className="rotate-180" size={18} />}
                             </button>
                             <button onClick={next} className="w-10 h-10 rounded-full bg-black/40 text-white flex items-center justify-center hover:bg-black/60 transition pointer-events-auto">
                               {isRTL ? <ChevronRight className="rotate-180" size={18} /> : <ChevronRight size={18} />}
                             </button>
                           </div>
                           {/* Dots Indicator */}
                           <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
                              {news.map((_, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => setActiveIdx(idx)}
                                  className={`w-2.5 h-2.5 rounded-full ${idx === activeIdx ? 'bg-[#10B981]' : 'bg-white/60'}`}
                                  aria-label={`slide-${idx + 1}`}
                                />
                              ))}
                           </div>
                      </div>
                  )}
              </div>
          </div>
      </section>
  )
}

function ServicesSection({ t, lang }) {
    const isRTL = t?.dir === 'rtl'
    return (
        <section id="services" className="py-16 bg-white">
            <div className="container mx-auto px-4">
                <SectionHeader title={t.services.title} icon={FileText} t={t.services} moreHref={"/login"} />
                <p className={`text-gray-500 mb-8 -mt-4 text-sm ${isRTL ? 'text-right' : 'text-left'}`}>{t.services.desc}</p>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {SERVICES_DATA.map(service => (
                        <div
                          key={service.id}
                          className={`bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-all relative flex flex-col min-h-[220px] ${isRTL ? 'text-right' : 'text-left'}`}
                          dir={isRTL ? 'rtl' : 'ltr'}
                        >
                            <div className={`flex mb-4 w-full ${isRTL ? 'justify-end' : 'justify-start'}`}>
                                <div className="w-10 h-10 rounded-full bg-green-50 flex items-center justify-center text-[#198754]">
                                    <service.icon size={20} />
                                </div>
                            </div>
                            <h3 className={`${isRTL ? 'text-right' : 'text-left'} font-bold text-gray-800 text-base mb-2`}>{service.title[lang]}</h3>
                            <p className={`${isRTL ? 'text-right' : 'text-left'} text-xs text-gray-500 mb-5 leading-relaxed`}>{service.subtitle[lang]}</p>
                            
                            <div className="mt-auto flex justify-start">
                                <button className="bg-[#198754] text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-[#146c43] transition-colors" onClick={() => window.location.href = service.url}>
                                    {t.services.details}
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
                <div className={`${isRTL ? 'text-right' : 'text-left'} mt-4 text-xs text-gray-400`}>{t.services.updated}</div>
            </div>
        </section>
    )
}

function EventsSection({ events = [], t, lang }) {
    // Always show the section; use a fallback event if none exist.
    const featuredEvent = events[0] || {
      title: t.events.title,
      desc: t.events.more,
      dateHijri: '',
      dateGreg: '',
      url: '#',
      status: t.events.status
    }
    const listEvents = events.slice(0, 8) // show last 8 (backend already orders desc)

    const pageSize = 4
    const totalPages = Math.max(1, Math.ceil(listEvents.length / pageSize))
    const [page, setPage] = useState(0)
    const pagedEvents = listEvents.slice(page * pageSize, page * pageSize + pageSize)

    return (
        <section id="events" className="py-16 bg-[#F8F9FA]">
            <div className="container mx-auto px-4">
                 <SectionHeader title={t.events.title} icon={Calendar} t={t.events} moreHref="https://www.fsf.gov.sa/media-center/forces-news" />
                 
                 {/* Featured Event Banner (light background, dynamic calendar) */}
                 <div className="rounded-2xl mb-8 flex flex-col lg:flex-row lg:items-center gap-8 bg-[#F8F9FA]">
                        <div className="flex-1 lg:order-2 flex justify-center">
                            <EventCalendar events={events} lang={lang} />
                        </div>
                        <div className="flex-1 lg:order-1 text-right">
                            <div className="text-gray-500 font-medium mb-2 dir-ltr text-right">
                                {featuredEvent.dateGreg} {featuredEvent.dateGreg && ' / '} {featuredEvent.dateHijri}
                            </div>
                            <h2 className="text-2xl font-bold text-gray-800 mb-4 leading-tight">
                                {featuredEvent.title}
                            </h2>
                            <p className="text-gray-500 mb-6">{featuredEvent.desc}</p>
                            <a
                              href={featuredEvent.url || '#'}
                              target={featuredEvent.url ? '_blank' : '_self'}
                              rel="noopener noreferrer"
                              className="inline-block bg-[#198754] text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-[#146c43] transition-colors"
                            >
                              {t.events.details}
                            </a>
                        </div>
                    </div>

                 {/* Events Grid (if there are any) */}
                 {listEvents.length > 0 && (
                   <>
                     <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        {pagedEvents.map(event => (
                            <a
                              key={event.id}
                              href={event.url || '#'}
                              target={event.url ? '_blank' : '_self'}
                              rel="noopener noreferrer"
                              className="bg-white border border-gray-100 rounded-xl p-5 shadow-sm block hover:shadow-md transition-shadow"
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <Calendar className="text-[#198754]" size={24} />
                                    <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">{event.status}</span>
                                </div>
                                <div className="text-right mb-3">
                                    <div className="font-bold text-gray-800">{event.day}</div>
                                    <div className="text-xs text-gray-500 dir-ltr">{event.dateGreg} / {event.dateHijri}</div>
                                </div>
                                <h4 className="text-sm font-bold text-gray-800 leading-relaxed mb-4 line-clamp-3">{event.title}</h4>
                            </a>
                        ))}
                     </div>
                     <div className="flex justify-center gap-2 mt-8">
                        {Array.from({ length: totalPages }).map((_, idx) => (
                          <button
                            key={idx}
                            onClick={() => setPage(idx)}
                            className={`w-2.5 h-2.5 rounded-full ${idx === page ? 'bg-[#198754]' : 'bg-gray-300'}`}
                            aria-label={`Page ${idx + 1}`}
                          />
                        ))}
                     </div>
                   </>
                 )}
            </div>
        </section>
    )
}

function ImportantLinks({ t }) {
  const scrollContainer = useRef(null)

  const scroll = (direction) => {
    if (scrollContainer.current) {
      const scrollAmount = 200
      const isRTL = document.dir === 'rtl'
      const modifier = isRTL ? -1 : 1
      
      scrollContainer.current.scrollBy({ 
        left: (direction === 'left' ? -scrollAmount : scrollAmount) * modifier, 
        behavior: 'smooth' 
      })
    }
  }

  return (
    <section id="links" className="py-16 bg-white border-t border-gray-100">
       <div className="container mx-auto px-4">
        <div className="flex items-center gap-4 mb-8">
          <div className="h-8 w-1 bg-[#198754] rounded-full shrink-0"></div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2 shrink-0">{t.links.title}</h2>
          <div className="flex-1 border-t-2 border-gray-200"></div>
        </div>
        <p className="text-gray-500 mb-10 -mt-4 pr-5">{t.links.desc}</p>

        <div className="relative group px-12">
          <button 
            onClick={() => scroll('right')}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-20 w-10 h-10 bg-white border border-gray-200 rounded-full flex items-center justify-center shadow-md hover:bg-gray-50"
          >
            <ChevronRight size={20} />
          </button>
          
          <div 
            ref={scrollContainer}
            className="flex gap-6 overflow-x-auto pb-4 scrollbar-hide snap-x"
            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
          >
            {IMPORTANT_LINKS.map(link => (
              <a 
                key={link.id} 
                href={link.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="min-w-[140px] h-[140px] border border-gray-200 rounded-xl flex flex-col items-center justify-center p-4 snap-start hover:border-fsf-primary transition-colors cursor-pointer block bg-white"
              >
                <img src={link.image} alt="" className="w-full h-full object-contain" />
              </a>
            ))}
          </div>

          <button 
            onClick={() => scroll('left')}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-20 w-10 h-10 bg-white border border-gray-200 rounded-full flex items-center justify-center shadow-md hover:bg-gray-50"
          >
            <ChevronLeft size={20} />
          </button>
        </div>
      </div>
    </section>
  )
}

function Footer({ t }) {
  return (
    <footer className="bg-[#1a3c33] text-white py-12 px-4">
      <div className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          {/* Column 1 */}
          <div>
            <h4 className="font-bold mb-4 text-[#a3b8b0]">{t.footer.overview}</h4>
            <ul className="space-y-2 text-sm text-[#d1dcd8]">
              <li><a href="#" className="hover:text-white transition-colors">{t.footer.about}</a></li>
              <li><a href="#" className="hover:text-white transition-colors">{t.footer.privacy}</a></li>
              <li><a href="#" className="hover:text-white transition-colors">{t.footer.news}</a></li>
            </ul>
          </div>
          
          {/* Column 2 */}
          <div>
            <h4 className="font-bold mb-4 text-[#a3b8b0]">{t.footer.contact}</h4>
            <ul className="space-y-2 text-sm text-[#d1dcd8]">
              <li><a href="#" className="hover:text-white transition-colors">{t.footer.connect}</a></li>
              <li><a href="#" className="hover:text-white transition-colors">{t.footer.share}</a></li>
              <li><a href="#" className="hover:text-white transition-colors">{t.footer.media}</a></li>
              <li><a href="#" className="hover:text-white transition-colors">{t.footer.innovation}</a></li>
            </ul>
          </div>

           {/* Column 3 - Social */}
           <div>
             <h4 className="font-bold mb-4 text-[#a3b8b0]">{t.footer.follow}</h4>
             <div className="flex gap-3">
               <a href="#" className="w-10 h-10 rounded-lg border border-[#3e665a] flex items-center justify-center hover:bg-[#3e665a] transition-colors">
                  <span className="text-xl">𝕏</span>
               </a>
               <a href="#" className="w-10 h-10 rounded-lg border border-[#3e665a] flex items-center justify-center hover:bg-[#3e665a] transition-colors">
                  <span className="text-xl">▶</span>
               </a>
             </div>
           </div>

           {/* Column 4 - Logo */}
           <div className="flex flex-col items-center md:items-end">
              <Logo className="w-48 h-48 mb-4" />
           </div>
        </div>

        <div className="border-t border-[#3e665a] pt-8 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex gap-6 text-xs text-[#d1dcd8]">
            <a href="#" className="hover:text-white">{t.footer.map}</a>
            <a href="#" className="hover:text-white">{t.footer.sla}</a>
            <a href="#" className="hover:text-white">{t.footer.rules}</a>
          </div>

          <div className="text-center md:text-left text-xs text-[#8ca39b]">
            <p className="mb-2">{t.footer.rights.replace('2025', new Date().getFullYear())}</p>
            <p>{t.footer.developed}</p>
            <p className="mt-1">{t.footer.updated}</p>
          </div>
          
           <div className="flex gap-4 opacity-50 grayscale hover:grayscale-0 hover:opacity-100 transition-all">
             <div className="h-8 w-12 bg-white/20 rounded"></div>
             <div className="h-8 w-12 bg-white/20 rounded"></div>
           </div>
        </div>
      </div>
    </footer>
  )
}

// =============================================================================
// MAIN APP WRAPPER
// =============================================================================

export default function Landing() {
  // 1. Persist language state
  const [lang, setLang] = useState(() => {
    return localStorage.getItem('app_lang') || 'ar'
  })
  
  const t = TEXTS[lang]
  
  const [alerts, setAlerts] = useState([])
  const [news, setNews] = useState([])
  const [events, setEvents] = useState([])

  const getDayName = (dateStr) => {
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString(lang === 'ar' ? 'ar-SA' : 'en-US', { weekday: 'long' });
    } catch {
        return '';
    }
  }
  
  const toggleLang = () => {
    setLang(prev => {
      const newLang = prev === 'ar' ? 'en' : 'ar'
      localStorage.setItem('app_lang', newLang)
      return newLang
    })
  }

  useEffect(() => {
    const fetchData = async () => {
        try {
            const alertsRes = await fetch(`${API_BASE}/${ENDPOINTS.ALERTS}`)
            const alertsData = await alertsRes.json()
            if (alertsData.message) {
                setAlerts(alertsData.message.map(a => ({
                    id: a.name || Math.random(),
                    title: {
                        en: a.warning_name_en || '',
                        ar: a.warning_name_ar || ''
                    },
                    description: {
                        en: a.warning_description_en || '',
                        ar: a.warning_description_ar || ''
                    },
                    recommendations: {
                        en: a.recommendations || '',
                        ar: a.recommendations_ar || ''
                    },
                    severity: a.severity_level, 
                    date: a.warning_date,
                    sectors: {
                        en: a.target_sectors_en || [],
                        ar: a.target_sectors_ar || []
                    },
                    iconUrl: a.warning_source_logo,
                    url: a.warning_link
                })))
            }

            const newsRes = await fetch(`${API_BASE}/${ENDPOINTS.NEWS}`)
            const newsData = await newsRes.json()
            if (newsData.message) {
                setNews(newsData.message.map(n => ({
                    id: n.name,
                    title: n.title,
                    desc: n.description,
                    image: n.image,
                    url: n.url,
                    date: n.date
                })))
            }

            const eventsRes = await fetch(`${API_BASE}/${ENDPOINTS.EVENTS}`)
            const eventsData = await eventsRes.json()
            if (eventsData.message) {
                setEvents(eventsData.message.map(e => ({
                    id: e.name || Math.random(),
                    title: e.event_title,
                    desc: e.event_description,
                    day: getDayName(e.event_date_gregorian),
                    dateHijri: e.event_date_hijri,
                    dateGreg: e.event_date_gregorian,
                    status: t.events.status,
                    image: e.event_image,
                    url: e.event_link
                })))
            }

        } catch (err) {
            console.error('Error fetching data:', err)
        }
    }
    fetchData()
  }, [lang, t.events.status]) // Remove lang dependency to avoid refetching on language change 

  return (
    <div dir={t.dir} className="min-h-screen font-sans text-gray-900 bg-white selection:bg-[#10B981] selection:text-white">
      <Navbar currentLang={lang} toggleLang={toggleLang} t={t} />
      <Hero t={t} />
      <AlertsSection alerts={alerts} t={t} lang={lang} />
      <NewsSection news={news} t={t} />
      <ServicesSection t={t} lang={lang} />
      <EventsSection events={events} t={t} lang={lang} />
      <ImportantLinks t={t} />
      <Footer t={t} />
    </div>
  )
}
