from app.services.fee_service import get_current_fees

CHAIN_META = {
    "ethereum": {
        "estimated_time_sec": 15,
        "speed_score": 5.0,
        "reliability_score": 10.0,
        "risk_score": 10.0,
        "risk_level": "low",
        "notes": "Most mature network, highest decentralization, but usually the most expensive."
    },
    "arbitrum": {
        "estimated_time_sec": 3,
        "speed_score": 9.0,
        "reliability_score": 9.0,
        "risk_score": 8.5,
        "risk_level": "medium-low",
        "notes": "Fast and cheap L2 with strong adoption. Still depends on L2 assumptions."
    },
    "base": {
        "estimated_time_sec": 2,
        "speed_score": 10.0,
        "reliability_score": 8.8,
        "risk_score": 8.3,
        "risk_level": "medium-low",
        "notes": "Very cheap and fast. Good UX. Slightly lower maturity than Ethereum mainnet."
    },
    "optimism": {
        "estimated_time_sec": 3,
        "speed_score": 8.8,
        "reliability_score": 8.9,
        "risk_score": 8.4,
        "risk_level": "medium-low",
        "notes": "Stable L2 with broad ecosystem adoption and relatively low fees."
    },
    "polygon": {
        "estimated_time_sec": 4,
        "speed_score": 8.5,
        "reliability_score": 8.4,
        "risk_score": 7.8,
        "risk_level": "medium",
        "notes": "Usually cheap and fast, but different native token economics and slightly different risk profile."
    },
}

# placeholder bridge assumptions for MVP v1
BRIDGE_META = {
    ("ethereum", "arbitrum"): {"bridge_cost_usd": 1.20, "bridge_time_sec": 420, "bridge_risk_score": 8.6},
    ("ethereum", "base"): {"bridge_cost_usd": 1.10, "bridge_time_sec": 360, "bridge_risk_score": 8.5},
    ("ethereum", "optimism"): {"bridge_cost_usd": 1.15, "bridge_time_sec": 420, "bridge_risk_score": 8.5},
    ("ethereum", "polygon"): {"bridge_cost_usd": 0.90, "bridge_time_sec": 300, "bridge_risk_score": 8.0},

    ("arbitrum", "ethereum"): {"bridge_cost_usd": 1.30, "bridge_time_sec": 600, "bridge_risk_score": 8.4},
    ("base", "ethereum"): {"bridge_cost_usd": 1.20, "bridge_time_sec": 540, "bridge_risk_score": 8.3},
    ("optimism", "ethereum"): {"bridge_cost_usd": 1.25, "bridge_time_sec": 600, "bridge_risk_score": 8.3},
    ("polygon", "ethereum"): {"bridge_cost_usd": 1.00, "bridge_time_sec": 360, "bridge_risk_score": 7.8},

    ("arbitrum", "base"): {"bridge_cost_usd": 0.85, "bridge_time_sec": 240, "bridge_risk_score": 8.2},
    ("base", "arbitrum"): {"bridge_cost_usd": 0.85, "bridge_time_sec": 240, "bridge_risk_score": 8.2},
    ("arbitrum", "optimism"): {"bridge_cost_usd": 0.90, "bridge_time_sec": 260, "bridge_risk_score": 8.1},
    ("optimism", "arbitrum"): {"bridge_cost_usd": 0.90, "bridge_time_sec": 260, "bridge_risk_score": 8.1},
    ("base", "optimism"): {"bridge_cost_usd": 0.80, "bridge_time_sec": 220, "bridge_risk_score": 8.1},
    ("optimism", "base"): {"bridge_cost_usd": 0.80, "bridge_time_sec": 220, "bridge_risk_score": 8.1},

    ("arbitrum", "polygon"): {"bridge_cost_usd": 0.95, "bridge_time_sec": 300, "bridge_risk_score": 7.9},
    ("polygon", "arbitrum"): {"bridge_cost_usd": 0.95, "bridge_time_sec": 300, "bridge_risk_score": 7.9},
    ("base", "polygon"): {"bridge_cost_usd": 0.90, "bridge_time_sec": 280, "bridge_risk_score": 7.9},
    ("polygon", "base"): {"bridge_cost_usd": 0.90, "bridge_time_sec": 280, "bridge_risk_score": 7.9},
    ("optimism", "polygon"): {"bridge_cost_usd": 0.95, "bridge_time_sec": 300, "bridge_risk_score": 7.9},
    ("polygon", "optimism"): {"bridge_cost_usd": 0.95, "bridge_time_sec": 300, "bridge_risk_score": 7.9},
}


def _calculate_cost_scores(routes):
    if not routes:
        return routes

    costs = [route["estimated_total_cost_usd"] for route in routes]
    min_cost = min(costs)
    max_cost = max(costs)

    for route in routes:
        if max_cost == min_cost:
            route["cost_score"] = 10.0
        else:
            normalized = (max_cost - route["estimated_total_cost_usd"]) / (max_cost - min_cost)
            route["cost_score"] = round(normalized * 10, 2)

    return routes


def _normalize_weights(cost_weight, speed_weight, reliability_weight, risk_weight):
    total = cost_weight + speed_weight + reliability_weight + risk_weight

    if total <= 0:
        return 0.4, 0.2, 0.2, 0.2

    return (
        cost_weight / total,
        speed_weight / total,
        reliability_weight / total,
        risk_weight / total,
    )


def _calculate_total_score(route, cost_weight, speed_weight, reliability_weight, risk_weight):
    total = (
        cost_weight * route["cost_score"] +
        speed_weight * route["speed_score"] +
        reliability_weight * route["reliability_score"] +
        risk_weight * route["risk_score"]
    )
    return round(total, 2)


def _build_direct_route(source_chain, destination_chain, fees, meta):
    source_fee = fees[source_chain]["estimated_usd"]

    return {
        "route_type": "direct",
        "source_chain": source_chain,
        "destination_chain": destination_chain,
        "execution_chain": source_chain,
        "estimated_network_fee_usd": source_fee,
        "estimated_bridge_cost_usd": 0.0,
        "estimated_total_cost_usd": round(source_fee, 6),
        "estimated_time_sec": meta["estimated_time_sec"],
        "speed_score": meta["speed_score"],
        "reliability_score": meta["reliability_score"],
        "risk_score": meta["risk_score"],
        "risk_level": meta["risk_level"],
        "notes": f"Direct transfer on {source_chain}. {meta['notes']}",
        "gas_gwei": fees[source_chain]["gas_gwei"],
        "latest_block": fees[source_chain]["latest_block"],
        "native_token_symbol": fees[source_chain].get("native_token_symbol"),
        "native_token_price_usd": fees[source_chain].get("native_token_price_usd"),
    }


def _build_cross_chain_route(source_chain, destination_chain, fees, meta, bridge_meta):
    source_fee = fees[source_chain]["estimated_usd"]
    destination_fee = fees[destination_chain]["estimated_usd"]

    bridge_cost = bridge_meta["bridge_cost_usd"]
    bridge_time = bridge_meta["bridge_time_sec"]
    bridge_risk_score = bridge_meta["bridge_risk_score"]

    total_cost = source_fee + bridge_cost + destination_fee
    total_time = meta["estimated_time_sec"] + bridge_time

    speed_score = max(1.0, round(meta["speed_score"] - min(4.0, bridge_time / 200), 2))
    risk_score = round((meta["risk_score"] + bridge_risk_score) / 2, 2)
    reliability_score = meta["reliability_score"]

    return {
        "route_type": "cross-chain",
        "source_chain": source_chain,
        "destination_chain": destination_chain,
        "execution_chain": destination_chain,
        "estimated_network_fee_usd": round(source_fee + destination_fee, 6),
        "estimated_bridge_cost_usd": round(bridge_cost, 6),
        "estimated_total_cost_usd": round(total_cost, 6),
        "estimated_time_sec": total_time,
        "speed_score": speed_score,
        "reliability_score": reliability_score,
        "risk_score": risk_score,
        "risk_level": meta["risk_level"],
        "notes": (
            f"Cross-chain transfer from {source_chain} to {destination_chain}. "
            f"Includes bridge assumptions for MVP. {meta['notes']}"
        ),
        "gas_gwei": fees[destination_chain]["gas_gwei"],
        "latest_block": fees[destination_chain]["latest_block"],
        "native_token_symbol": fees[destination_chain].get("native_token_symbol"),
        "native_token_price_usd": fees[destination_chain].get("native_token_price_usd"),
    }


def calculate_best_route(req):
    cost_weight, speed_weight, reliability_weight, risk_weight = _normalize_weights(
        req.cost_weight,
        req.speed_weight,
        req.reliability_weight,
        req.risk_weight
    )

    fees = get_current_fees()

    available_chains = {
        chain: data for chain, data in fees.items() if data.get("status") == "ok"
    }

    if req.source_chain not in available_chains:
        return {"error": f"Source chain '{req.source_chain}' is unavailable"}

    if req.destination_chain not in available_chains:
        return {"error": f"Destination chain '{req.destination_chain}' is unavailable"}

    routes = []

    if req.source_chain == req.destination_chain:
        meta = CHAIN_META.get(req.source_chain)
        if not meta:
            return {"error": f"No metadata available for chain '{req.source_chain}'"}

        routes.append(
            _build_direct_route(
                source_chain=req.source_chain,
                destination_chain=req.destination_chain,
                fees=available_chains,
                meta=meta,
            )
        )
    else:
        direct_bridge_key = (req.source_chain, req.destination_chain)
        destination_meta = CHAIN_META.get(req.destination_chain)

        if not destination_meta:
            return {"error": f"No metadata available for chain '{req.destination_chain}'"}

        if direct_bridge_key in BRIDGE_META:
            routes.append(
                _build_cross_chain_route(
                    source_chain=req.source_chain,
                    destination_chain=req.destination_chain,
                    fees=available_chains,
                    meta=destination_meta,
                    bridge_meta=BRIDGE_META[direct_bridge_key],
                )
            )

        # also compare "move funds to each possible destination chain" when destination differs
        # this gives optional alternatives if source->destination is not the only candidate
        for candidate_chain in available_chains:
            if candidate_chain == req.source_chain:
                continue

            candidate_meta = CHAIN_META.get(candidate_chain)
            if not candidate_meta:
                continue

            bridge_key = (req.source_chain, candidate_chain)
            if bridge_key not in BRIDGE_META:
                continue

            routes.append(
                _build_cross_chain_route(
                    source_chain=req.source_chain,
                    destination_chain=candidate_chain,
                    fees=available_chains,
                    meta=candidate_meta,
                    bridge_meta=BRIDGE_META[bridge_key],
                )
            )

    if not routes:
        return {
            "error": "No available transfer plans"
        }

    # deduplicate by source/destination/route_type
    deduped = {}
    for route in routes:
        key = (route["source_chain"], route["destination_chain"], route["route_type"])
        if key not in deduped or route["estimated_total_cost_usd"] < deduped[key]["estimated_total_cost_usd"]:
            deduped[key] = route

    routes = list(deduped.values())
    routes = _calculate_cost_scores(routes)

    for route in routes:
        route["total_score"] = _calculate_total_score(
            route,
            cost_weight,
            speed_weight,
            reliability_weight,
            risk_weight
        )

    routes = sorted(routes, key=lambda x: x["total_score"], reverse=True)

    best = routes[0]
    alternatives = routes[1:]

    return {
        "request": {
            "token": req.token,
            "amount": req.amount,
            "source_chain": req.source_chain,
            "destination_chain": req.destination_chain
        },
        "weights": {
            "cost_weight": round(cost_weight, 3),
            "speed_weight": round(speed_weight, 3),
            "reliability_weight": round(reliability_weight, 3),
            "risk_weight": round(risk_weight, 3)
        },
        "best_route": best,
        "alternatives": alternatives,
        "summary": {
            "recommended_chain": best["destination_chain"],
            "route_type": best["route_type"],
            "reason": (
                f"Best transfer plan based on weighted cost, speed, reliability, and risk "
                f"({best['total_score']}/10)"
            )
        }
    }