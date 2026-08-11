from setuptools import setup, find_packages

setup(
    name='custom_fsf',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "pypdf>=3.0.0",
        "reportlab>=4.0.0",
        "hijridate>=2.3.0",
        "razorpay>=2.0.0",
    ],
    entry_points={
        'console_scripts': [
            'patch-lms = custom_fsf.commands.patch_lms:run_patch',
        ]
    },
    package_data={
        'custom_fsf': ['patches.txt']
    },
)
