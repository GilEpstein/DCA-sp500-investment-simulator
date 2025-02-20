import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# פונקציה לטעינת הנתונים
@st.cache
def load_data():
    df = pd.read_csv("data/sp500_data.csv", parse_dates=["Date"])
    df.set_index("Date", inplace=True)
    return df

def simulate_investment(df, start_date, end_date, base_investment=100, threshold=0.2, boost_pct=0.2):
    """
    סימולציה:
    1. בכל חודש מתבצעת השקעה של base_investment (100$).
    2. אם מחיר הסגירה של סוף החודש נמוך מ-(1 - threshold) * (השיא ב-52 השבועות הקודמים),
       ההשקעה באותו חודש מוגדלת ב-boost_pct (למשל, מ-100$ ל-120$).

    :param df: DataFrame עם נתוני SP500 (עמודת Close)
    :param start_date: תאריך התחלה לסימולציה
    :param end_date: תאריך סיום לסימולציה
    :param base_investment: ההשקעה הבסיסית בכל חודש (100$)
    :param threshold: אחוז ירידה – לדוגמה, 0.2 עבור 20%
    :param boost_pct: אחוז ההגדלה – לדוגמה, 0.2 עבור 20%
    :return: DataFrame עם תוצאות הסימולציה
    """
    df_period = df[(df.index >= start_date) & (df.index <= end_date)]
    monthly_dates = pd.date_range(start=start_date, end=end_date, freq='MS')
    total_shares = 0.0
    records = []
    
    for date in monthly_dates:
        # קבלת המחיר של סוף החודש (אם לא קיים, משתמשים במחיר הקרוב ביותר)
        if date in df_period.index:
            current_price = df_period.loc[date, 'Close']
        else:
            current_price = df_period['Close'].asof(date)
        
        invest_amount = base_investment
        
        # בדיקה: האם המחיר הנוכחי נמוך מ-(1 - threshold) מהשיא ב-52 השבועות הקודמים?
        start_52 = date - pd.DateOffset(weeks=52)
        period_52 = df[(df.index >= start_52) & (df.index < date)]
        if not period_52.empty:
            high_52 = period_52['Close'].max()
            if current_price <= (1 - threshold) * high_52:
                invest_amount = base_investment * (1 + boost_pct)
        
        shares_bought = invest_amount / current_price
        total_shares += shares_bought
        portfolio_value = total_shares * current_price
        
        records.append({
            'Date': date,
            'Monthly Investment': invest_amount,
            'Cumulative Invested': invest_amount if len(records)==0 else None,
            'Portfolio Value': portfolio_value
        })
    
    result_df = pd.DataFrame(records)
    result_df['Cumulative Invested'] = result_df['Monthly Investment'].cumsum()
    result_df.set_index('Date', inplace=True)
    return result_df

def plot_simulation(sim_df, title):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sim_df.index, sim_df['Portfolio Value'], marker='o')
    ax.set_title(title)
    ax.set_xlabel("תאריך")
    ax.set_ylabel("שווי תיק ($)")
    st.pyplot(fig)

# התחלת האפליקציה עם Streamlit
st.title("סימולטור השקעות ב-SP500 עם התאמות לפי ירידה במחיר")
st.markdown("""
האפליקציה מדמה השקעה חודשית קבועה של 100$ ברכישת מניות SP500.  
בנוסף, אם מחיר הסגירה של החודש ירד מתחת ב-Y% מהשיא ב-52 השבועות,  
האפליקציה תגדיל את ההשקעה ב-Z%.

**להצטרפות לקבוצת הווטסאפ שלי:**  
[לחץ כאן להצטרפות](https://chat.whatsapp.com/KPhdGsFcR9Q6jYcgmeYckM)
""")

# קלט מהמשתמש: ערכי Y ו-Z
threshold = st.number_input("Y - אחוז הירידה (למשל, 20 עבור 20%)", value=20.0, min_value=0.0) / 100
boost_pct = st.number_input("Z - אחוז ההגדלה (למשל, 20 עבור 20%)", value=20.0, min_value=0.0) / 100

# בחירת התקופות לסימולציה
period_options = ["5 שנים", "10 שנים", "15 שנים", "20 שנים"]
selected_periods = st.multiselect("בחר את התקופות לסימולציה", period_options, default=period_options)

# טעינת הנתונים
df = load_data()
end_date = df.index.max()

# חישוב תאריך ההתחלה עבור כל תקופה
periods_dates = {}
for period in selected_periods:
    years = int(period.split()[0])
    start_date = end_date - pd.DateOffset(years=years)
    periods_dates[period] = start_date

st.header("תוצאות הסימולציה")
results = {}

for period, start_date in periods_dates.items():
    sim_df = simulate_investment(df, start_date, end_date, base_investment=100, threshold=threshold, boost_pct=boost_pct)
    final_value = sim_df["Portfolio Value"].iloc[-1]
    total_invested = sim_df["Cumulative Invested"].iloc[-1]
    st.markdown(f"**{period}:** השקעה כוללת: {total_invested:.2f}$, שווי תיק: {final_value:.2f}$")
    plot_simulation(sim_df, f"סימולציה עבור {period}")
    results[period] = (total_invested, final_value)
