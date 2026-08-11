"""
Custom FSF — Arabic translation manager.

Translation DocType entries are loaded by Frappe AFTER all ar.csv files
(including ERPNext's), so these always win regardless of app install order
or Docker image build sequence.

To add/change a translation: edit TRANSLATIONS below, then run:
    bench --site <site> migrate
"""

import frappe

LANG = "ar"

TRANSLATIONS = {
    # ── Standard Asset field labels (override ERPNext's defaults) ────────────
    "ID":                        "المعرف",
    "Company":                   "الشركة",
    "Item Code":                 "كود الصنف",
    "Asset Name":                "اسم الأصل",
    "Asset Category":            "فئة الأصل",
    "Location":                  "الموقع",
    "Net Purchase Amount":       "إجمالي مبلغ الشراء",
    "Purchase Date":             "تاريخ الشراء",
    "Available-for-use Date":    "تاريخ الإتاحة للاستخدام",
    "Is Existing Asset":         "أصل موجود",
    "Status":                    "الحالة",
    "Custodian":                 "المكلف",
    "Department":                "القسم",
    "Cost Center":               "مركز التكلفة",

    # ── Brand names that must not be translated ───────────────────────────────
    "Excel":                     "Excel",      # Microsoft Excel — not an Arabic word

    # ── Export UI ─────────────────────────────────────────────────────────────
    "Sr":                        "م",
    "Export Data":               "تصدير البيانات",
    "Export":                    "تصدير",
    "File Type":                 "نوع الملف",
    "Export Type":               "نوع التصدير",
    "All Records":               "جميع السجلات",
    "Filtered Records":          "السجلات المصفاة",
    "5 Records":                 "5 سجلات",
    "Blank Template":            "قالب فارغ",
    "Exporting...":              "جارٍ التصدير...",
    "Uncategorized":             "غير مصنف",
    "No data provided":          "لم يتم تقديم بيانات",
    "No data to export":         "لا توجد بيانات للتصدير",

    # ── Asset category field validation ───────────────────────────────────────
    "Field '{0}' is required.":
        "الحقل '{0}' مطلوب.",
    "Field '{0}' must be a number.":
        "يجب أن يكون الحقل '{0}' رقمًا.",
    "Field '{0}' must be a valid date.":
        "يجب أن يكون الحقل '{0}' تاريخًا صحيحًا.",
    "Field '{0}' must be one of: {1}":
        "يجب أن تكون قيمة الحقل '{0}' إحدى: {1}",
    "Duplicate field label '{0}' found in row {1}. Each field must have a unique label.":
        "تسمية الحقل '{0}' مكررة في الصف {1}. يجب أن تكون لكل حقل تسمية فريدة.",
    "Duplicate Field":
        "حقل مكرر",
    "Duplicate field name '{0}' found in row {1}. Each field must have a unique name.":
        "اسم الحقل '{0}' مكرر في الصف {1}. يجب أن يكون لكل حقل اسم فريد.",
    "Synchronized from Asset Category Field Values for Data Import/Export.":
        "متزامن من قيم حقول فئة الأصل للاستيراد/التصدير.",

    # ── Asset management ──────────────────────────────────────────────────────
    "Cannot scrap asset '{0}' because it has a custodian assigned ({1}). Please clear the custodian first.":
        "لا يمكن إتلاف الأصل '{0}' لأنه مسند إلى ({1}). يرجى إزالة المكلف أولاً.",
    "Cannot sell asset '{0}' because it has a custodian assigned ({1}). Please clear the custodian first.":
        "لا يمكن بيع الأصل '{0}' لأنه مسند إلى ({1}). يرجى إزالة المكلف أولاً.",
    "Cannot sell asset '{0}' because it has a custodian assigned to {1}. Please clear the custodian field before selling.":
        "لا يمكن بيع الأصل '{0}' لأنه مسند إلى {1}. يرجى إزالة المكلف قبل البيع.",
    "Cannot move asset '{0}' because it has status '{1}'. Only active assets can be moved or assigned.":
        "لا يمكن نقل الأصل '{0}' لأن حالته '{1}'. يمكن نقل الأصول النشطة فقط.",
    "Invalid Asset Status":      "حالة الأصل غير صحيحة",
    "Asset already has no custodian.":
        "الأصل ليس له مكلف مسبقًا.",
    "Asset returned by clearing custodian":
        "تم إرجاع الأصل بإزالة المكلف",

    # ── Scrap Asset dialog ────────────────────────────────────────────────────
    "Enter date to scrap asset":
        "أدخل تاريخ إتلاف الأصل",
    "Select the date":           "اختر التاريخ",
    "Scrap date cannot be before purchase date":
        "لا يمكن أن يكون تاريخ الإتلاف قبل تاريخ الشراء",
    "Do you really want to scrap this asset?":
        "هل تريد بالتأكيد إتلاف هذا الأصل؟",

    # ── Split Asset dialog ────────────────────────────────────────────────────
    "Split Asset":               "تقسيم الأصل",
    "Split Qty":                 "كمية التقسيم",
    "Split":                     "تقسيم",

    # ── Generic dialog action ─────────────────────────────────────────────────
    "Submit":                    "إرسال",
    "Return":                    "إرجاع",
    "Are you sure you want to return this asset?":
        "هل تريد إرجاع هذا الأصل؟",
    "Asset returned":            "تم إرجاع الأصل",
    "Enter number":              "أدخل رقمًا",
    "Must be a number":          "يجب أن يكون رقمًا",
    "Select...":                 "اختر...",
    "Enter value":               "أدخل القيمة",
    "For Select fields, add options in the 'Options' column (one per line)":
        "لحقول الاختيار، أضف الخيارات في عمود 'خيارات' (خيار واحد في كل سطر)",
    "Changing field name from '{0}' to '{1}' will affect {2} asset(s). The existing data will be migrated. Continue?":
        "تغيير اسم الحقل من '{0}' إلى '{1}' سيؤثر على {2} أصل. سيتم ترحيل البيانات. هل تريد المتابعة؟",
    "This field has data in {0} asset(s). Deleting it will remove all related data. Are you sure?":
        "يحتوي هذا الحقل على بيانات في {0} أصل. حذفه سيزيل كل البيانات المرتبطة. هل أنت متأكد؟",

    # ── HD Ticket ─────────────────────────────────────────────────────────────
    "Only agents can change ticket status.":
        "يمكن للوكلاء فقط تغيير حالة التذكرة.",
    "New tickets must start with status Open.":
        "يجب أن تبدأ التذاكر الجديدة بحالة مفتوح.",
    "Only agents can assign tickets.":
        "يمكن للوكلاء فقط تعيين التذاكر.",
    "Closed tickets cannot be modified.":
        "لا يمكن تعديل التذاكر المغلقة.",
    "Ticket can only be closed after it is resolved.":
        "لا يمكن إغلاق التذكرة إلا بعد حلها.",
    "Please assign this ticket to a team or an agent before moving it to In Progress":
        "يرجى تعيين هذه التذكرة لفريق أو وكيل قبل نقلها إلى قيد التنفيذ",
    "Cannot change status from {0} to {1}. Allowed transitions: {2}":
        "لا يمكن تغيير الحالة من {0} إلى {1}. التحولات المسموحة: {2}",
    "Ticket {0} has been assigned to you":
        "تم تعيين التذكرة {0} إليك",
    "Ticket {0} has been assigned to your team {1}":
        "تم تعيين التذكرة {0} إلى فريقك {1}",
    "Ticket {0} status changed to {1}":
        "تم تغيير حالة التذكرة {0} إلى {1}",
    "Ticket {0} has been assigned to {1}":
        "تم تعيين التذكرة {0} إلى {1}",
    "Comment added successfully":
        "تمت إضافة التعليق بنجاح",
    "Ticket reassigned successfully":
        "تمت إعادة تعيين التذكرة بنجاح",
    "Closed tickets do not accept requester replies. Please contact support to reopen.":
        "التذاكر المغلقة لا تقبل ردود الطالب. يرجى التواصل مع الدعم لإعادة فتحها.",
    "Add Internal Comment":      "إضافة تعليق داخلي",
    "Reassign":                  "إعادة التعيين",
    "Reassign Ticket":           "إعادة تعيين التذكرة",
    "New Agent":                 "وكيل جديد",
    "New Team":                  "فريق جديد",
    "Start Working":             "بدء العمل",
    "Resolve":                   "حل",
    "Need More Info":            "بحاجة لمزيد من المعلومات",
    "Waiting Approval":          "في انتظار الموافقة",
    "Resume Work":               "استئناف العمل",
    "Reopen":                    "إعادة فتح",
    "In Progress":               "قيد التنفيذ",
    "Resolved":                  "محلول",

    # ── HD Dashboard ──────────────────────────────────────────────────────────
    "Dashboard":                 "لوحة التحكم",
    "Period":                    "الفترة",
    "Agent":                     "الوكيل",
    "Clear Filters":             "مسح الفلاتر",
    "Tickets Trend":             "اتجاه التذاكر",
    "Feedback Trend":            "اتجاه ردود الفعل",
    "Tickets by Status":         "التذاكر حسب الحالة",
    "Tickets by Priority":       "التذاكر حسب الأولوية",
    "Tickets by Department":     "التذاكر حسب القسم",
    "Tickets by Team":           "التذاكر حسب الفريق",
    "Tickets by Type":           "التذاكر حسب النوع",
    "Total Tickets":             "إجمالي التذاكر",
    "% Resolved":                "% محلول",
    "% SLA Fulfilled":           "% تحقق مستوى الخدمة",
    "Avg. Resolution Time":      "متوسط وقت الحل",
    "Avg. Active Time":          "متوسط وقت النشاط",
    "No ticket data for this period":
        "لا توجد بيانات تذاكر لهذه الفترة",
    "No feedback data for this period":
        "لا توجد بيانات تغذية راجعة لهذه الفترة",
    "Avg Rating":                "متوسط التقييم",
    "No data available":         "لا توجد بيانات",
    "Not authorized to view dashboard":
        "غير مصرح لك بعرض لوحة التحكم",
    "days":                      "أيام",
    "hrs":                       "ساعات",
    "mins":                      "دقائق",
    "tickets":                   "تذاكر",

    # ── Audit Log ─────────────────────────────────────────────────────────────
    "Document Created":          "تم إنشاء المستند",
    "Document Deleted":          "تم حذف المستند",
    "Values Changed":            "القيم المعدلة",
    "Rows Added":                "الصفوف المضافة",
    "Rows Removed":              "الصفوف المحذوفة",
    "Row Values Changed":        "قيم الصف المعدلة",
    "Original Value":            "القيمة الأصلية",
    "New Value":                 "القيمة الجديدة",
    "Via Data Import":           "عبر استيراد البيانات",
    "Audit logs cannot be created manually for security reasons.":
        "لا يمكن إنشاء سجلات المراجعة يدويًا لأسباب أمنية.",
    "Audit logs cannot be modified for security reasons.":
        "لا يمكن تعديل سجلات المراجعة لأسباب أمنية.",
    "Audit logs cannot be deleted. Use archival instead.":
        "لا يمكن حذف سجلات المراجعة. استخدم الأرشفة بدلاً من ذلك.",

    # ── User / Roles ───────────────────────────────────────────────────────────
    "Role Profile is required":
        "ملف الأدوار مطلوب",
    "Role Profile Not Found":
        "ملف الأدوار غير موجود",
    "Asset Manager":             "مدير الأصول",
    "Import Row Errors":         "أخطاء في صف الاستيراد",

    # ── Project ────────────────────────────────────────────────────────────────
    "New Lessons Learned":       "درس مستفاد جديد",
    "Lessons Learned":           "الدروس المستفادة",
    "New Project Recommendation": "توصية مشروع جديدة",
    "Project Recommendation":    "توصيات المشروع",
    "New Client Evaluation":     "تقييم عميل جديد",
    "Client Evaluations":        "تقييمات العملاء",
    "Evaluation Summary":        "ملخص التقييم",
    "Language updated. Reloading...":
        "تم تحديث اللغة. جارٍ إعادة التحميل...",

    # ── Reports ────────────────────────────────────────────────────────────────
    "Main Category":             "الفئة الرئيسية",
    "Custom Field":              "حقل مخصص",
    "Custom Field Value":        "قيمة الحقل المخصص",

    # ── Library ────────────────────────────────────────────────────────────────
    "Not permitted to download this document":
        "غير مصرح لك بتنزيل هذا المستند",
    "No file attached to this Library record":
        "لا يوجد ملف مرفق بهذا السجل في المكتبة",

    # ── Data Import / Export UI (Frappe core strings) ─────────────────────────
    "Show Only Failed Logs":     "عرض السجلات الفاشلة فقط",
    "Row Number":                "رقم الصف",
    "Successfully imported {0}": "تم استيراد {0} بنجاح",
    "Successfully updated {0}":  "تم تحديث {0} بنجاح",
    # {0} is a raw English verb ("imported"/"updated") — use {1} (count) only
    "Successfully {0} 1 record.":     "تم معالجة سجل واحد بنجاح.",
    "Successfully {0} {1} records.":  "تم معالجة {1} سجل بنجاح.",
    "Successfully {0} {1} record out of {2}. Click on Export Errored Rows, fix the errors and import again.":
        "تم معالجة {1} سجل من أصل {2} بنجاح. انقر على تصدير الصفوف الخطأ، وقم بتصحيح الأخطاء ثم أعد الاستيراد.",
    "Successfully {0} {1} records out of {2}. Click on Export Errored Rows, fix the errors and import again.":
        "تم معالجة {1} سجل من أصل {2} بنجاح. انقر على تصدير الصفوف الخطأ، وقم بتصحيح الأخطاء ثم أعد الاستيراد.",
    "The following values are invalid: {0}. Values must be one of {1}":
        "القيم التالية غير صالحة: {0}. يجب أن تكون إحدى: {1}",
    "Value must be one of {0}":  "يجب أن تكون القيمة إحدى: {0}",
    "Cannot match column {0} with any field":
        "لا يمكن مطابقة العمود {0} بأي حقل",
    "Skipping Duplicate Column {0}":
        "تخطي العمود المكرر {0}",
    "Date format could not be determined from the values in this column. Defaulting to yyyy-mm-dd.":
        "تعذر تحديد صيغة التاريخ من قيم هذا العمود. سيتم استخدام yyyy-mm-dd افتراضيًا.",
    "Import Successful":         "تم الاستيراد بنجاح",
    "Import Failed":             "فشل الاستيراد",
    "Preparing Rows":            "جارٍ تحضير الصفوف",
    "Importing":                 "جارٍ الاستيراد",
    "Export Import Log":         "تصدير سجل الاستيراد",
    "Go to {0} List":            "الانتقال إلى قائمة {0}",
    "Import template should be of type .csv, .xlsx or .xls":
        "يجب أن يكون قالب الاستيراد من نوع .csv أو .xlsx أو .xls",
    "Import template should contain a Header and atleast one row.":
        "يجب أن يحتوي قالب الاستيراد على رأس وصف على الأقل.",
    "Import timed out, please re-try.":
        "انتهت مهلة الاستيراد، يرجى المحاولة مجددًا.",
    "Importing {0} of {1}, {2}": "جارٍ استيراد {0} من {1}، {2}",
    "Updating {0} of {1}, {2}":  "جارٍ تحديث {0} من {1}، {2}",
    "Skipping {0} of {1}, {2}":  "تخطي {0} من {1}، {2}",
    "Invalid or corrupted content for import":
        "محتوى غير صالح أو تالف للاستيراد",
    "Invalid template file for import":
        "ملف قالب غير صالح للاستيراد",
    "Loading import file...":    "جارٍ تحميل ملف الاستيراد...",
    "Mapping column {0} to field {1}":
        "ربط العمود {0} بالحقل {1}",
    "No changes to update":      "لا توجد تغييرات للتحديث",
    "No failed logs":            "لا توجد سجلات فاشلة",
    "Row {0}":                   "الصف {0}",
    "Show Traceback":            "عرض تتبع الخطأ",
    "Skipping Untitled Column":  "تخطي العمود بلا عنوان",
    "Skipping column {0}":       "تخطي العمود {0}",
    "Successfully updated {0}":  "تم تحديث {0} بنجاح",
    "Successfully {0} 1 record.":    "تم {0} سجل واحد بنجاح.",
    "Successfully {0} {1} records.": "تم {0} {1} سجل بنجاح.",
    "Template Error":            "خطأ في القالب",
    "The column {0} has {1} different date formats. Automatically setting {2} as the default format as it is the most common. Please change other values in this column to this format.":
        "يحتوي العمود {0} على {1} صيغ تاريخ مختلفة. تم تعيين {2} كصيغة افتراضية لكونها الأكثر شيوعًا. يرجى تغيير القيم الأخرى إلى هذه الصيغة.",
    "The following values do not exist for {0}: {1}":
        "القيم التالية غير موجودة للحقل {0}: {1}",
    "Value {0} missing for {1}": "القيمة {0} مفقودة للحقل {1}",
    "Value {0} must be in the valid duration format: d h m s":
        "يجب أن تكون القيمة {0} بالصيغة الصحيحة للمدة: d h m s",
    "Value {0} must in {1} format":
        "يجب أن تكون القيمة {0} بصيغة {1}",
    "via Data Import":           "عبر استيراد البيانات",
}


def apply_translations():
    """
    Upsert every entry in TRANSLATIONS into the Translation DocType.
    Runs automatically on after_migrate and after_install.
    Can also be called manually:  bench execute custom_fsf.translations_manager.apply_translations
    """
    if not frappe.db.exists("DocType", "Translation"):
        return

    new_count = updated_count = 0

    for source_text, translated_text in TRANSLATIONS.items():
        existing = frappe.db.get_value(
            "Translation",
            {"language": LANG, "source_text": source_text},
            ["name", "translated_text"],
            as_dict=True,
        )

        if existing:
            if existing.translated_text != translated_text:
                frappe.db.set_value("Translation", existing.name, "translated_text", translated_text)
                updated_count += 1
        else:
            frappe.get_doc({
                "doctype": "Translation",
                "language": LANG,
                "source_text": source_text,
                "translated_text": translated_text,
            }).insert(ignore_permissions=True)
            new_count += 1

    if new_count or updated_count:
        frappe.db.commit()
        # Clear the merged translation cache so changes take effect immediately
        frappe.cache.delete_keys("lang:")
        frappe.logger().info(
            f"[custom_fsf] translations: {new_count} added, {updated_count} updated"
        )
