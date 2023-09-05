from setuptools import setup


requires = [
    "kafka-python>=2.0.2",
    "numpy>=1.25.2",
    "omegaconf>=2.3.0",
    "opencv-python==4.8.0.74",
    "pandas>=2.0.3",
    "Pillow>=10.0.0",
    "requests>=2.31.0",
    "shapely>=2.0.1",
    "tornado>=6.3.2",
    "urllib3>=2.0.4"
]
readme = open('README.md').read()
license = open("LICENSE").read()

setup(
    name='zutils',
    version='1.0.1',
    description='the utils for me',
    long_description=readme,
    long_description_content_type="text/markdown",
    author='zhouxianggen',
    author_email='zhouxianggen@gmail.com',
    url='https://github.com/zhouxianggen/zutils',
    packages=["zutils", "zutils/web_service", "zutils/processor"],
    package_dir={"": "src"},
    python_requires=">=3.7",
    install_requires=requires,
    license=license
)
