import json
import requests
import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="ChainRoute Pro",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Session state init
# -----------------------------
defaults = {
    "last_quote": None,
    "cost_weight": 40,
    "speed_weight": 20,
    "reliability_weight": 20,
    "risk_weight": 20,
    "last_quote_time": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -----------------------------
# Auto refresh
# -----------------------------
st_autorefresh(interval=15000, key="fees_refresh")

# -----------------------------
# Branding / Assets
# -----------------------------
CHAIN_META = {
    "ethereum": {
        "name": "Ethereum",
        "logo": "https://cdn.simpleicons.org/ethereum/627EEA",
        "accent": "#627EEA",
    },
    "arbitrum": {
        "name": "Arbitrum",
        "logo": "https://cdn.simpleicons.org/arbitrum/2D374B",
        "accent": "#28A0F0",
    },
    "base": {
        "name": "Base",
        "logo": "https://cdn.simpleicons.org/base/0052FF",
        "accent": "#0052FF",
    },
    "optimism": {
        "name": "Optimism",
        "logo": "https://cdn.simpleicons.org/optimism/FF0420",
        "accent": "#FF0420",
    },
    "polygon": {
        "name": "Polygon",
        "logo": "https://cdn.simpleicons.org/polygon/8247E5",
        "accent": "#8247E5",
    },
}

CHAIN_ORDER = ["ethereum", "arbitrum", "base", "optimism", "polygon"]

# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .app-hero {
        padding: 1.2rem 1.2rem 1rem 1.2rem;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        background: linear-gradient(135deg, rgba(20,24,40,0.95), rgba(30,40,70,0.95));
        margin-bottom: 1rem;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.25rem;
    }
    .hero-subtitle {
        color: #AEB7C6;
        font-size: 1rem;
        margin-bottom: 0.4rem;
    }
    .hero-badge {
        display: inline-block;
        padding: 0.3rem 0.7rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.08);
        color: #D7DEEA;
        font-size: 0.85rem;
        margin-right: 0.4rem;
    }
    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0.25rem 0 0.7rem 0;
    }
    .soft-card {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 1rem;
        background: rgba(255,255,255,0.02);
        margin-bottom: 0.8rem;
    }
    .best-card {
        border: 1px solid rgba(98,126,234,0.35);
        border-radius: 22px;
        padding: 1rem 1rem 0.8rem 1rem;
        background: linear-gradient(135deg, rgba(98,126,234,0.10), rgba(130,71,229,0.10));
        margin-bottom: 1rem;
    }
    .mini-label {
        color: #9BA6B7;
        font-size: 0.82rem;
        margin-bottom: 0.1rem;
    }
    .mini-value {
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 0.4rem;
    }
    .chain-pill {
        display:inline-block;
        padding:0.28rem 0.65rem;
        border-radius:999px;
        background:rgba(255,255,255,0.06);
        border:1px solid rgba(255,255,255,0.08);
        font-size:0.86rem;
        margin-right:0.35rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Helpers
# -----------------------------
def chain_name(chain: str) -> str:
    return CHAIN_META.get(chain, {}).get("name", chain.capitalize())

def chain_logo(chain: str) -> str:
    return CHAIN_META.get(chain, {}).get("logo", "")

def risk_badge(level: str) -> str:
    mapping = {
        "low": "🟢 low",
        "medium-low": "🟡 medium-low",
        "medium": "🟠 medium",
        "high": "🔴 high",
    }
    return mapping.get(level, f"⚪ {level}")

def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default

def render_chain_header(chain: str):
    c1, c2 = st.columns([1, 5])
    with c1:
        st.image(chain_logo(chain), width=28)
    with c2:
        st.markdown(f"**{chain_name(chain)}**")

# -----------------------------
# Data load
# -----------------------------
fees = {}
try:
    fees_response = requests.get(f"{API_BASE}/fees/current", timeout=10)
    fees_response.raise_for_status()
    fees = fees_response.json()
except Exception as e:
    st.error(f"Failed to load current fees: {e}")

ok_fees = {chain: data for chain, data in fees.items() if data.get("status") == "ok"}

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## 💠 ChainRoute Pro")
    st.caption("Transfer planning engine")
    st.markdown("---")

    token = st.selectbox("Token", ["USDC"])
    amount = st.number_input("Amount", min_value=1.0, value=5000.0, step=100.0)

    source_chain = st.selectbox(
        "Source Chain",
        CHAIN_ORDER,
        format_func=chain_name
    )

    destination_chain = st.selectbox(
        "Destination Chain",
        CHAIN_ORDER,
        index=2,
        format_func=chain_name
    )

    st.markdown("### Scoring Weights")
    st.slider("Cost", min_value=0, max_value=100, step=5, key="cost_weight")
    st.slider("Speed", min_value=0, max_value=100, step=5, key="speed_weight")
    st.slider("Reliability", min_value=0, max_value=100, step=5, key="reliability_weight")
    st.slider("Risk", min_value=0, max_value=100, step=5, key="risk_weight")

    total_weight = (
        st.session_state.cost_weight +
        st.session_state.speed_weight +
        st.session_state.reliability_weight +
        st.session_state.risk_weight
    )

    if total_weight == 0:
        st.warning("At least one weight must be greater than 0.")

    if st.button("Calculate Transfer Plan", use_container_width=True):
        payload = {
            "token": token,
            "amount": amount,
            "source_chain": source_chain,
            "destination_chain": destination_chain,
            "cost_weight": st.session_state.cost_weight,
            "speed_weight": st.session_state.speed_weight,
            "reliability_weight": st.session_state.reliability_weight,
            "risk_weight": st.session_state.risk_weight
        }

        try:
            quote_response = requests.post(f"{API_BASE}/route/quote", json=payload, timeout=10)
            quote_response.raise_for_status()
            st.session_state.last_quote = quote_response.json()
            st.session_state.last_quote_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            st.error(f"Failed to get transfer plan: {e}")

    if st.button("Clear Plan", use_container_width=True):
        st.session_state.last_quote = None
        st.session_state.last_quote_time = None

    st.markdown("---")
    st.caption("Auto-refresh every 15 seconds")

# -----------------------------
# Hero
# -----------------------------
st.markdown(
    """
    <div class="app-hero">
        <div class="hero-title">ChainRoute Pro</div>
        <div class="hero-subtitle">
            Find the most cost-effective transfer path across major chains with live fees, weighted scoring, and transfer plan comparison.
        </div>
        <span class="hero-badge">Live fees</span>
        <span class="hero-badge">Risk-aware scoring</span>
        <span class="hero-badge">Transfer planning</span>
        <span class="hero-badge">Export ready</span>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# KPI row
# -----------------------------
if ok_fees:
    sorted_fees = sorted(ok_fees.items(), key=lambda x: x[1]["estimated_usd"])
    cheapest_chain, cheapest_data = sorted_fees[0]
    expensive_chain, expensive_data = sorted_fees[-1]
    spread = safe_float(expensive_data["estimated_usd"]) - safe_float(cheapest_data["estimated_usd"])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Cheapest Chain", chain_name(cheapest_chain))
    k2.metric("Lowest Fee", f"${cheapest_data['estimated_usd']}")
    k3.metric("Most Expensive", chain_name(expensive_chain))
    k4.metric("Fee Spread", f"${round(spread, 6)}")

    st.caption(f"Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.warning("No healthy chain data available right now.")

st.markdown("---")

# -----------------------------
# Chain health cards
# -----------------------------
st.markdown('<div class="section-title">Chain Health Summary</div>', unsafe_allow_html=True)
health_cols = st.columns(len(CHAIN_ORDER))

for idx, chain in enumerate(CHAIN_ORDER):
    with health_cols[idx]:
        data = fees.get(chain)
        with st.container():
            st.markdown('<div class="soft-card">', unsafe_allow_html=True)
            render_chain_header(chain)

            if not data:
                st.error("No data")
            elif data.get("status") == "ok":
                st.success("Healthy")
                st.caption(f"Fee ${data['estimated_usd']}")
                st.caption(f"Gas {data['gas_gwei']} Gwei")
            else:
                st.error(data.get("error", "Unknown error"))

            st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Main two-column area
# -----------------------------
left_col, right_col = st.columns([1.05, 1])

with left_col:
    st.markdown('<div class="section-title">Current Network Fees</div>', unsafe_allow_html=True)

    for chain in CHAIN_ORDER:
        data = fees.get(chain)

        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        render_chain_header(chain)

        if not data:
            st.error("No data")
        elif data.get("status") == "ok":
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="mini-label">Native Token</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="mini-value">{data.get("native_token_symbol", "-")}</div>', unsafe_allow_html=True)
                st.markdown('<div class="mini-label">Estimated Fee</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="mini-value">${data.get("estimated_usd", "-")}</div>', unsafe_allow_html=True)
                st.markdown('<div class="mini-label">Gas</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="mini-value">{data.get("gas_gwei", "-")} Gwei</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="mini-label">Token Price</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="mini-value">${data.get("native_token_price_usd", "-")}</div>', unsafe_allow_html=True)
                st.markdown('<div class="mini-label">Latest Block</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="mini-value">{data.get("latest_block", "-")}</div>', unsafe_allow_html=True)
                if "rpc_used" in data:
                    st.caption("RPC connected")
        else:
            st.error(data.get("error", "Unknown error"))

        st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="section-title">Best Transfer Plan</div>', unsafe_allow_html=True)

    if st.session_state.last_quote:
        quote = st.session_state.last_quote

        if "error" in quote:
            st.error(quote["error"])
        else:
            best = quote["best_route"]

            st.markdown('<div class="best-card">', unsafe_allow_html=True)
            top1, top2 = st.columns([6, 1])
            with top1:
                st.markdown("### 🏆 Recommended Plan")
            with top2:
                st.image(chain_logo(best["destination_chain"]), width=34)

            st.write(
                f"**{chain_name(best['source_chain'])} → {chain_name(best['destination_chain'])}**"
            )
            st.markdown(
                f'<span class="chain-pill">{best["route_type"]}</span>'
                f'<span class="chain-pill">{chain_name(best["execution_chain"])}</span>',
                unsafe_allow_html=True
            )

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Cost", f"${best['estimated_total_cost_usd']}")
            m2.metric("Bridge Cost", f"${best['estimated_bridge_cost_usd']}")
            m3.metric("ETA", f"{best['estimated_time_sec']} sec")

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Cost", f"{best['cost_score']}/10")
            s2.metric("Speed", f"{best['speed_score']}/10")
            s3.metric("Reliability", f"{best['reliability_score']}/10")
            s4.metric("Risk", f"{best['risk_score']}/10")

            st.write(f"**Risk Level:** {risk_badge(best['risk_level'])}")
            st.write(f"**Total Score:** {best['total_score']}/10")
            st.write(quote["summary"]["reason"])
            st.info(best["notes"])

            if "weights" in quote:
                st.caption(
                    f"Weights → Cost: {quote['weights']['cost_weight']}, "
                    f"Speed: {quote['weights']['speed_weight']}, "
                    f"Reliability: {quote['weights']['reliability_weight']}, "
                    f"Risk: {quote['weights']['risk_weight']}"
                )

            if st.session_state.last_quote_time:
                st.caption(f"Last calculated plan: {st.session_state.last_quote_time}")

            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.info("Use the left sidebar to calculate a transfer plan.")
        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Comparison section
# -----------------------------
st.markdown("---")
st.markdown('<div class="section-title">Transfer Plan Comparison</div>', unsafe_allow_html=True)

if st.session_state.last_quote and "error" not in st.session_state.last_quote:
    quote = st.session_state.last_quote
    all_routes = [quote["best_route"]] + quote["alternatives"]

    comparison_rows = []
    for idx, route in enumerate(all_routes, start=1):
        comparison_rows.append({
            "Rank": idx,
            "Route Type": route["route_type"],
            "Source": chain_name(route["source_chain"]),
            "Destination": chain_name(route["destination_chain"]),
            "Execution Chain": chain_name(route["execution_chain"]),
            "Native Token": route["native_token_symbol"],
            "Network Fee (USD)": route["estimated_network_fee_usd"],
            "Bridge Cost (USD)": route["estimated_bridge_cost_usd"],
            "Total Cost (USD)": route["estimated_total_cost_usd"],
            "ETA (sec)": route["estimated_time_sec"],
            "Cost Score": route["cost_score"],
            "Speed Score": route["speed_score"],
            "Reliability Score": route["reliability_score"],
            "Risk Score": route["risk_score"],
            "Risk Level": route["risk_level"],
            "Total Score": route["total_score"],
            "Notes": route["notes"],
            "Best": "Yes" if idx == 1 else "No"
        })

    comparison_df = pd.DataFrame(comparison_rows)
    st.dataframe(comparison_df, use_container_width=True, height=320)

    c1, c2 = st.columns([1.2, 0.8])

    with c1:
        st.markdown("### Score Comparison")
        chart_df = comparison_df.set_index("Destination")[
            ["Total Score", "Cost Score", "Speed Score", "Reliability Score", "Risk Score"]
        ]
        st.bar_chart(chart_df, use_container_width=True)

    with c2:
        st.markdown("### Export")
        csv_data = comparison_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Comparison CSV",
            data=csv_data,
            file_name="transfer_comparison.csv",
            mime="text/csv",
            use_container_width=True
        )

        json_data = json.dumps(comparison_rows, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            label="Download Comparison JSON",
            data=json_data,
            file_name="transfer_comparison.json",
            mime="application/json",
            use_container_width=True
        )
else:
    st.info("Calculate a transfer plan first to see the comparison table.")

# -----------------------------
# Historical analytics
# -----------------------------
st.markdown("---")
st.markdown('<div class="section-title">Historical Analytics</div>', unsafe_allow_html=True)

try:
    history_response = requests.get(f"{API_BASE}/fees/history", timeout=10)
    history_response.raise_for_status()
    history = history_response.json()

    rows = []
    for snapshot in history:
        ts = datetime.fromtimestamp(snapshot["timestamp"])
        snapshot_fees = snapshot.get("fees", {})

        for chain, data in snapshot_fees.items():
            if data.get("status") == "ok":
                rows.append({
                    "timestamp": ts,
                    "chain": chain,
                    "estimated_usd": data["estimated_usd"],
                    "gas_gwei": data["gas_gwei"]
                })

    if rows:
        df = pd.DataFrame(rows)
        df = (
            df.groupby(["timestamp", "chain"], as_index=False)
            .agg({
                "estimated_usd": "mean",
                "gas_gwei": "mean"
            })
            .sort_values("timestamp")
        )

        tab1, tab2, tab3 = st.tabs(["Fee Trend", "Gas Trend", "Raw History"])

        with tab1:
            fee_pivot = df.pivot(index="timestamp", columns="chain", values="estimated_usd")
            fee_pivot = fee_pivot.rename(columns={c: chain_name(c) for c in fee_pivot.columns})
            st.line_chart(fee_pivot, use_container_width=True)

        with tab2:
            gas_pivot = df.pivot(index="timestamp", columns="chain", values="gas_gwei")
            gas_pivot = gas_pivot.rename(columns={c: chain_name(c) for c in gas_pivot.columns})
            st.line_chart(gas_pivot, use_container_width=True)

        with tab3:
            latest_df = df.sort_values("timestamp", ascending=False).head(30).copy()
            latest_df["chain"] = latest_df["chain"].apply(chain_name)
            st.dataframe(latest_df, use_container_width=True)

            history_csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Fee History CSV",
                data=history_csv,
                file_name="fee_history.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("No history data yet. Refresh the app a few times first.")

except Exception as e:
    st.error(f"Failed to load history: {e}")