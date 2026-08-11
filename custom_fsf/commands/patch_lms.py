import os
import subprocess

def patch_show_toast(path):
    with open(path, 'r+') as f:
        content = f.read()
        if "export function showToast(" in content:
            print("✅ showToast already exists.")
            return

        toast_function = '''
export function showToast(title, text, icon, iconClasses = null) {
    if (!iconClasses) {
        if (icon == 'check') {
            iconClasses = 'bg-surface-green-3 text-ink-white rounded-md p-px'
        } else if (icon == 'alert-circle') {
            iconClasses = 'bg-yellow-600 text-ink-white rounded-md p-px'
        } else {
            iconClasses = 'bg-surface-red-5 text-ink-white rounded-md p-px'
        }
    }
    createToast({
        title: title,
        text: htmlToText(text),
        icon: icon,
        iconClasses: iconClasses,
        position: icon == 'check' ? 'bottom-right' : 'top-center',
        timeout: 5,
    })
}
'''
        # Move cursor to end and append
        f.seek(0, os.SEEK_END)
        f.write('\n\n' + toast_function.strip() + '\n')
        print("✅ showToast function appended at the end.")


def enable_symlink(path):
    with open(path, 'r+') as f:
        content = f.read()
        if 'preserveSymlinks' in content:
            print("`preserveSymlinks` already set.")
            return

        # Insert the line after the `alias` block or at the top of `resolve`
        updated = ''
        lines = content.splitlines()
        for i, line in enumerate(lines):
            updated += line + '\n'
            if 'alias' in line and '{' in line:
                # Look ahead for closing brace of alias block
                brace_count = 1
                for j in range(i+1, len(lines)):
                    updated += lines[j] + '\n'
                    if '{' in lines[j]:
                        brace_count += 1
                    if '}' in lines[j]:
                        brace_count -= 1
                        if brace_count == 0:
                            # Inject preserveSymlinks here
                            updated += '    preserveSymlinks: true,\n'
                            break
                break

        # Append the rest of the content
        rest = '\n'.join(lines[j+1:])
        updated += rest

        # Write back
        f.seek(0)
        f.write(updated)
        f.truncate()
        print("✅ `preserveSymlinks: true` added.")

        
def install_vue_router(bench_root):
    frontend_path = os.path.join(bench_root, "apps/lms/frontend")
    node_modules_path = os.path.join(frontend_path, "node_modules/vue-router")
    if os.path.exists(node_modules_path):
        print("🔁 vue-router already installed.")
        return
    try:
        print("📦 Installing vue-router...")
        subprocess.run(["yarn", "add", "vue-router@4"], cwd=frontend_path, check=True)
        print("✅ vue-router installed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install vue-router: {e}")

def patch_main_js(path):
    css_import = "import '../../lms/public/css/lms_overrides.css';\n"
    with open(path, 'r+') as f:
        lines = f.readlines()
        if css_import.strip() in "".join(lines):
            print("✅ CSS import already exists.")
            return
        for i, line in enumerate(lines):
            if "import './index.css'" in line:
                lines.insert(i + 1, css_import)
                print("✅ Inserted CSS import.")
                break
        f.seek(0)
        f.writelines(lines)
        f.truncate()

def patch_sidebar(path):
    new_links = [
        """		{
			label: 'Home',
			icon: 'Home',
			to: 'Home',
			activeFor: ['Home'],
		},""",
        """		{
			label: 'Podcasts',
			icon: 'Mic',
			to: 'Podcasts',
			activeFor: ['Podcasts'],
		},"""
    ]
    with open(path, 'r+') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "return [" in line and "getSidebarLinks" in "".join(lines[:i]):
                for block in reversed(new_links):
                    if block.strip() not in "".join(lines):
                        lines.insert(i + 1, block + '\n')
                        print(f"✅ Inserted sidebar block: {block.strip().splitlines()[0]}")
                break
        f.seek(0)
        f.writelines(lines)
        f.truncate()
        
def patch_router(path):
    with open(path, 'r+') as f:
        lines = f.readlines()
        content = "".join(lines)

        # 1. Update defaultRoute to /home
        if "let defaultRoute = '/courses'" in content:
            content = content.replace("let defaultRoute = '/courses'", "let defaultRoute = '/home'")
            lines = content.splitlines(keepends=True)
            print("✅ Updated defaultRoute to '/home'")

        # 2. Insert /home route if not exists
        if "path: '/home'," not in content:
            home_route = """
\t{
\t\tpath: '/home',
\t\tname: 'Home',
\t\tcomponent: () => import('@/pages/App_fsf.vue'),
\t},
"""
            insert_index = next(i for i, line in enumerate(lines) if "const routes = [" in line)
            lines.insert(insert_index + 1, home_route)
            print("✅ Inserted /home route")

        # 3. Insert /podcasts route directly after /courses block
        if "'/podcasts'" not in content:
            podcasts_route = """
\t{
\t\tpath: '/podcasts',
\t\tname: 'Podcasts',
\t\tcomponent: () => import('@/pages/App_fsf.vue'),
\t},
"""
            for i, line in enumerate(lines):
                if "path: '/courses'" in line:
                    # Now find the end of that block (a line that has just "},")
                    for j in range(i, len(lines)):
                        if lines[j].strip() == "},":
                            lines.insert(j + 1, podcasts_route)
                            print("✅ Inserted /podcasts route after /courses block")
                            break
                    break

        f.seek(0)
        f.writelines(lines)
        f.truncate()

def create_symlink(source, destination):
    if not os.path.exists(source):
        print(f"⚠️ Source not found, skipping: {source}")
        return

    # Delete existing file if it's not a symlink
    if os.path.exists(destination) and not os.path.islink(destination):
        os.remove(destination)
        print(f"🧹 Deleted: {destination}")

    # Only create symlink if it doesn't exist
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

    # Enable frontend build with symlinks
    enable_symlink(os.path.join(bench_root, "apps/lms/frontend/vite.config.js"))
    print("✅ LMS custom patch applied")


def run_patch():
    bench_root = "/home/frappe/frappe-bench/" ## Change it to real path
    install_vue_router(bench_root)
    symlink(bench_root)

    patch_main_js(os.path.join(bench_root, "apps/lms/frontend/src/main.js"))
    patch_sidebar(os.path.join(bench_root, "apps/lms/frontend/src/utils/index.js"))
    patch_router(os.path.join(bench_root, "apps/lms/frontend/src/router.js"))
    patch_show_toast(os.path.join(bench_root, "apps/lms/frontend/src/utils/index.js"))

if __name__ == "__main__":
    run_patch()
