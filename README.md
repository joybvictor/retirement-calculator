# 💰 Retirement Calculator

A comprehensive retirement planning calculator with advanced features including 401(k) projections, Social Security optimization, tax calculations, Medicare costs, and Required Minimum Distributions (RMDs).

🌐 **Live Demo:** [SmartRetire.Tools](https://smartretire.tools)

---

## ✨ Features

- **401(k) Projections**: Calculate growth with annual contributions and compound interest
- **Social Security Optimizer**: See benefits at different claiming ages (62, 65, 67, 70)
- **Pension Calculator**: Adjust for early retirement penalties
- **Tax Calculations**: Federal and state taxes with standard deductions
- **Medicare & Healthcare**: Includes Part B, Part D, and IRMAA surcharges
- **RMD Compliance**: Required Minimum Distributions starting at age 73
- **Inflation Adjustments**: All income sources adjust annually
- **Year-by-Year Breakdown**: Detailed amortization schedule
- **Multiple Scenarios**: Compare retirement at different ages
- **CSV Export**: Download results for further analysis

---

## 🚀 Quick Start

### Run Locally

```bash
# Clone the repository
git clone https://github.com/yourusername/retirement-calculator.git
cd retirement-calculator

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run retirement_calculator_streamlit.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📊 How It Works

### Input Parameters

- **Current age** and retirement age scenarios
- **401(k) balance** and annual contributions
- **Expected return rate** (default 7%)
- **Pension amount** at full retirement
- **Social Security benefits** at Full Retirement Age (FRA)
- **Tax rates** (federal marginal and state)
- **Life expectancy** for projections

### Calculations

1. **401(k) Growth**: `Balance × (1 + rate)^years + contributions`
2. **Social Security**: Adjusted by claiming age (70% at 62, 124% at 70)
3. **Pension**: Adjusted by retirement age (80% at 62, 100% at 67+)
4. **Taxes**: Progressive calculation with standard deductions
5. **Medicare**: Age 65+ with IRMAA surcharges based on income
6. **RMDs**: Age 73+ using IRS Uniform Lifetime Table
7. **Inflation**: All income sources increase annually

---

## 🛠️ Technology Stack

- **Python 3.10+**
- **Streamlit** - Web application framework
- **Pandas** - Data manipulation and analysis
- **Type Hints** - For code clarity and maintainability

---

## 📁 Project Structure

```
retirement-calculator/
├── retirement_calculator_streamlit.py  # Main application
├── requirements.txt                    # Python dependencies
└── README.md                          # This file
```

---

## 💡 Usage Examples

### Basic Retirement Planning
```python
# Input your information in the sidebar:
- Current Age: 45
- Current 401(k): $250,000
- Annual Contribution: $20,000
- Expected Return: 7%
- Pension (FRA): $2,000/month
- Social Security (FRA): $2,500/month
```

### View Results
- Compare retirement ages (62, 65, 67, 70)
- See net monthly and annual income
- Review year-by-year breakdown
- Download CSV reports

---

## 🎯 Key Assumptions

### Social Security
- Full Retirement Age (FRA): 67 (for most users)
- Early claiming (62): 70% of FRA benefit
- Delayed claiming (70): 124% of FRA benefit
- Up to 85% taxable based on combined income

### Pension
- 20% reduction at age 62
- 7% reduction at age 65
- 100% at age 67+

### Taxes
- Standard deduction: $14,600 (single)
- Additional $1,950 if age 65+
- Marginal rates: 10%, 12%, 22%, 24%, 32%, 35%, 37%

### Medicare (Age 65+)
- Part B: $174.70/month base
- Part D: ~$55/month
- IRMAA surcharges for higher incomes
- Out-of-pocket: ~$2,000/year

### RMDs (Age 73+)
- Based on IRS Uniform Lifetime Table
- Divisor decreases with age (26.5 at 73, 20.2 at 80)
- Must withdraw annually

---

## ⚠️ Important Disclaimers

**Educational Tool Only**: This calculator is for educational and informational purposes only. It does not constitute financial advice.

**Not Professional Advice**: Results are estimates based on assumptions you provide. Actual outcomes may vary significantly based on:
- Market performance
- Tax law changes
- Personal circumstances
- Inflation rates
- Healthcare costs
- Life expectancy

**Consult Professionals**: For personalized financial planning, consult with:
- Certified Financial Planner (CFP)
- Tax professional (CPA)
- Estate planning attorney

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests (if implemented)
pytest tests/
```

---

## 📝 License

This project is open source and available for personal and educational use.

---

## 👤 Author

**Joy Victor**

- Created in honor of Deiva Victor
- Clinical Research & AI Implementation Specialist
- DV Strategic Services

---

## 🌟 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - Beautiful web apps
- [Pandas](https://pandas.pydata.org/) - Data analysis
- IRS tax tables and guidelines
- Social Security Administration data

---

## 📞 Support

- **Website**: [smartretire.tools](https://smartretire.tools)
- **Issues**: [GitHub Issues](https://github.com/yourusername/retirement-calculator/issues)
- **Email**: joy@smartretire.tools

---

## 🔄 Version History

### v1.0.0 (2025-01-31)
- Initial release
- Core retirement calculations
- Social Security optimization
- Tax and Medicare calculations
- RMD compliance
- Inflation adjustments
- Year-by-year breakdown
- CSV export

---

## 🚀 Roadmap

Future enhancements planned:
- [ ] Roth IRA vs Traditional comparison
- [ ] HSA integration
- [ ] Monte Carlo simulations
- [ ] Part-time work scenarios
- [ ] Spouse/survivor benefits
- [ ] State-specific tax rules
- [ ] Investment allocation suggestions
- [ ] Mobile app version

---

**Made with ❤️ in honor of Deiva Victor**

*Empowering smart financial planning through data-driven tools*
