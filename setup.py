"""
Setup configuration for solar-quant package
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
readme_file = Path(__file__).parent / "energy_derivatives" / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')
else:
    long_description = "Solar energy derivatives pricing framework with NASA satellite data integration"

setup(
    name="solar-quant",
    version="0.2.0",
    description="Quantitative pricing framework for solar energy derivatives using NASA satellite data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Solarpunk Bitcoin Team",
    author_email="contact@solarpunk.example.com",  # Update with real email
    url="https://github.com/YOUR_USERNAME/solarpunk-bitcoin",  # Update with real URL
    project_urls={
        "Bug Reports": "https://github.com/YOUR_USERNAME/solarpunk-bitcoin/issues",
        "Source": "https://github.com/YOUR_USERNAME/solarpunk-bitcoin",
        "Documentation": "https://github.com/YOUR_USERNAME/solarpunk-bitcoin/blob/main/energy_derivatives/README.md",
    },

    # Package structure
    packages=find_packages(where="energy_derivatives"),
    package_dir={"": "energy_derivatives"},

    # Python version requirement
    python_requires=">=3.8",

    # Core dependencies
    install_requires=[
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "requests>=2.26.0",
        "scipy>=1.7.0",
    ],

    # Optional dependencies for different use cases
    extras_require={
        # Visualization dependencies
        "viz": [
            "matplotlib>=3.4.0",
            "seaborn>=0.11.0",
        ],

        # Development dependencies
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "ipython>=8.0.0",
            "jupyter>=1.0.0",
        ],

        # API server dependencies
        "api": [
            "fastapi>=0.95.0",
            "uvicorn>=0.21.0",
            "pydantic>=1.10.0",
        ],

        # Dashboard dependencies
        "dashboard": [
            "streamlit>=1.20.0",
            "plotly>=5.13.0",
        ],

        # Full installation (everything)
        "all": [
            "matplotlib>=3.4.0",
            "seaborn>=0.11.0",
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "fastapi>=0.95.0",
            "uvicorn>=0.21.0",
            "streamlit>=1.20.0",
            "plotly>=5.13.0",
        ],
    },

    # Package classification
    classifiers=[
        # Development status
        "Development Status :: 4 - Beta",

        # Intended audience
        "Intended Audience :: Science/Research",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",

        # Topics
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering :: Physics",

        # License
        "License :: OSI Approved :: MIT License",

        # Python versions
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",

        # Operating systems
        "Operating System :: OS Independent",

        # Framework
        "Framework :: FastAPI",
    ],

    # Keywords for PyPI search
    keywords=[
        "solar",
        "energy",
        "derivatives",
        "pricing",
        "quantitative-finance",
        "renewable-energy",
        "NASA",
        "satellite-data",
        "volatility",
        "options-pricing",
        "monte-carlo",
        "binomial-tree",
    ],

    # Entry points for command-line tools
    entry_points={
        "console_scripts": [
            "solar-quant=solar_quant.cli:main",  # To be implemented
        ],
    },

    # Include package data (config files, etc.)
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.json", "*.md"],
    },

    # Zip safety
    zip_safe=False,
)
