import os

def create_symlink(source, destination):
    if not os.path.exists(source):
        print(f"⚠️ Source not found, skipping: {source}")
        return

    if os.path.exists(destination) and not os.path.islink(destination):
        os.remove(destination)
        print(f"🧹 Deleted: {destination}")

    if not os.path.exists(destination):
        os.symlink(source, destination)
        print(f"🔗 Symlink created: {destination} -> {source}")

def symlink(bench_root):
    sources_and_destinations = [
        # Vue Pages & Components
        ("apps/custom_fsf/frontend/src/App_fsf.vue", "apps/lms/frontend/src/pages/App_fsf.vue"),
        ("apps/custom_fsf/frontend/src/components/Batches_fsf.vue", "apps/lms/frontend/src/components/Batches_fsf.vue"),
        ("apps/custom_fsf/frontend/src/components/CourseGrid_fsf.vue", "apps/lms/frontend/src/components/CourseGrid_fsf.vue"),
        ("apps/custom_fsf/frontend/src/components/Enrollments_fsf.vue", "apps/lms/frontend/src/components/Enrollments_fsf.vue"),
        ("apps/custom_fsf/frontend/src/components/HeroSection_fsf.vue", "apps/lms/frontend/src/components/HeroSection_fsf.vue"),
        ("apps/custom_fsf/frontend/src/components/CertificationLinks_fsf.vue", "apps/lms/frontend/src/components/CertificationLinks.vue"),
        ("apps/custom_fsf/frontend/src/components/CourseCardOverlay_fsf.vue", "apps/lms/frontend/src/components/CourseCardOverlay.vue"),
        ("apps/custom_fsf/frontend/src/pages/Notifications_fsf.vue", "apps/lms/frontend/src/pages/Notifications.vue"),
        ("apps/custom_fsf/frontend/src/pages/Lesson_fsf.vue", "apps/lms/frontend/src/pages/Lesson.vue"),

        # Assets
        ("apps/custom_fsf/frontend/src/assets/Courses.png", "apps/lms/frontend/src/assets/Courses.png"),
        ("apps/custom_fsf/frontend/src/assets/Podcast.png", "apps/lms/frontend/src/assets/Podcast.png"),

        # CSS & Scripts
        ("apps/custom_fsf/custom_fsf/public/css/lms_overrides.css", "apps/lms/lms/public/css/lms_overrides.css"),
        ("apps/custom_fsf/custom_fsf/scripts/utils_fsf.py", "apps/lms/lms/lms/utils.py"),
    ]

    for src_rel, dest_rel in sources_and_destinations:
        src = os.path.join(bench_root, src_rel)
        dest = os.path.join(bench_root, dest_rel)
        create_symlink(src, dest)

    print("🔁 LMS symlinks re-applied.")

if __name__ == "__main__":
    bench_root = "/home/frappe/frappe-bench"
    symlink(bench_root)
