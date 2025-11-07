"""
Comprehensive commodity and input cost tracking data
Organized by industry with impact mappings
"""

# ==================== COMMODITY SERIES ====================
COMMODITY_SERIES = {
    # ===== ENERGY =====
    "Crude_Oil_WTI": {
        "fred_id": "DCOILWTICO",
        "label": "Crude Oil (WTI)",
        "unit": "$/barrel",
        "category": "Energy"
    },
    "Crude_Oil_Brent": {
        "fred_id": "DCOILBRENTEU",
        "label": "Crude Oil (Brent)",
        "unit": "$/barrel",
        "category": "Energy"
    },
    "Natural_Gas": {
        "fred_id": "DHHNGSP",
        "label": "Natural Gas (Henry Hub)",
        "unit": "$/MMBtu",
        "category": "Energy"
    },
    "Gasoline": {
        "fred_id": "GASREGW",
        "label": "Gasoline (Regular)",
        "unit": "$/gallon",
        "category": "Energy"
    },
    "Heating_Oil": {
        "fred_id": "DHOILNYH",
        "label": "Heating Oil",
        "unit": "$/gallon",
        "category": "Energy"
    },
    "Propane": {
        "fred_id": "DPROPANEMBTX",
        "label": "Propane",
        "unit": "$/gallon",
        "category": "Energy"
    },
    
    # ===== METALS & MINING =====
    "Copper": {
        "fred_id": "PCOPPUSDM",
        "label": "Copper",
        "unit": "$/metric ton",
        "category": "Metals"
    },
    "Aluminum": {
        "fred_id": "PALUMUSDM",
        "label": "Aluminum",
        "unit": "$/metric ton",
        "category": "Metals"
    },
    "Iron_Ore": {
        "fred_id": "PIORECRUSDM",
        "label": "Iron Ore",
        "unit": "$/metric ton",
        "category": "Metals"
    },
    "Steel_Import": {
        "fred_id": "IQ12260",
        "label": "Steel Import Prices",
        "unit": "Index",
        "category": "Metals"
    },
    "Nickel": {
        "fred_id": "PNICKUSDM",
        "label": "Nickel",
        "unit": "$/metric ton",
        "category": "Metals"
    },
    "Zinc": {
        "fred_id": "PZINCUSDM",
        "label": "Zinc",
        "unit": "$/metric ton",
        "category": "Metals"
    },
    "Lead": {
        "fred_id": "PLEADUSDM",
        "label": "Lead",
        "unit": "$/metric ton",
        "category": "Metals"
    },
    "Tin": {
        "fred_id": "PTINUSDM",
        "label": "Tin",
        "unit": "$/metric ton",
        "category": "Metals"
    },
    
    # ===== PRECIOUS METALS =====
    "Gold": {
        "fred_id": "GOLDAMGBD228NLBM",
        "label": "Gold",
        "unit": "$/troy oz",
        "category": "Precious Metals"
    },
    "Silver": {
        "fred_id": "SLVPRUSD",
        "label": "Silver",
        "unit": "$/troy oz",
        "category": "Precious Metals"
    },
    "Platinum": {
        "fred_id": "PLATINUMPRICE",
        "label": "Platinum",
        "unit": "$/troy oz",
        "category": "Precious Metals"
    },
    "Palladium": {
        "fred_id": "PALLFMUSD",
        "label": "Palladium",
        "unit": "$/troy oz",
        "category": "Precious Metals"
    },
    
    # ===== AGRICULTURE - GRAINS =====
    "Wheat": {
        "fred_id": "PWHEAMTUSDM",
        "label": "Wheat",
        "unit": "$/metric ton",
        "category": "Agriculture - Grains"
    },
    "Corn": {
        "fred_id": "PMAIZMTUSDM",
        "label": "Corn (Maize)",
        "unit": "$/metric ton",
        "category": "Agriculture - Grains"
    },
    "Soybeans": {
        "fred_id": "PSOYBUSDM",
        "label": "Soybeans",
        "unit": "$/metric ton",
        "category": "Agriculture - Grains"
    },
    "Rice": {
        "fred_id": "PRICENPQUSDM",
        "label": "Rice",
        "unit": "$/metric ton",
        "category": "Agriculture - Grains"
    },
    "Barley": {
        "fred_id": "PBARLUSDM",
        "label": "Barley",
        "unit": "$/metric ton",
        "category": "Agriculture - Grains"
    },
    
    # ===== AGRICULTURE - SOFT COMMODITIES =====
    "Coffee": {
        "fred_id": "PCOFFOTMUSDM",
        "label": "Coffee (Arabica)",
        "unit": "$/kg",
        "category": "Agriculture - Soft"
    },
    "Cocoa": {
        "fred_id": "PCOCOCUSDM",
        "label": "Cocoa Beans",
        "unit": "$/metric ton",
        "category": "Agriculture - Soft"
    },
    "Sugar": {
        "fred_id": "PSUGAISAUSDM",
        "label": "Sugar",
        "unit": "$/kg",
        "category": "Agriculture - Soft"
    },
    "Cotton": {
        "fred_id": "PCOTTINDUSDM",
        "label": "Cotton",
        "unit": "$/kg",
        "category": "Agriculture - Soft"
    },
    "Orange_Juice": {
        "fred_id": "POJUICEUSDM",
        "label": "Orange Juice",
        "unit": "$/metric ton",
        "category": "Agriculture - Soft"
    },
    
    # ===== AGRICULTURE - LIVESTOCK =====
    "Beef": {
        "fred_id": "PBEEFUSDM",
        "label": "Beef",
        "unit": "$/kg",
        "category": "Agriculture - Livestock"
    },
    "Pork": {
        "fred_id": "PPORKUSDM",
        "label": "Pork (Swine)",
        "unit": "$/kg",
        "category": "Agriculture - Livestock"
    },
    "Chicken": {
        "fred_id": "PPOULT01USM156NNBR",
        "label": "Chicken (Poultry)",
        "unit": "$/pound",
        "category": "Agriculture - Livestock"
    },
    
    # ===== CONSTRUCTION MATERIALS =====
    "Lumber": {
        "fred_id": "WPU0811",
        "label": "Lumber",
        "unit": "Index",
        "category": "Construction"
    },
    "Cement": {
        "fred_id": "PCU32731273127",
        "label": "Cement Prices",
        "unit": "Index",
        "category": "Construction"
    },
    
    # ===== CHEMICALS & PLASTICS =====
    "Crude_Oil_Chemicals": {
        "fred_id": "WPU0613",
        "label": "Chemicals & Allied Products",
        "unit": "Index",
        "category": "Chemicals"
    },
    "Plastics": {
        "fred_id": "WPU0719",
        "label": "Plastic Resins & Materials",
        "unit": "Index",
        "category": "Chemicals"
    },
    
    # ===== TEXTILES & MATERIALS =====
    "Rubber": {
        "fred_id": "PRUBBUSDM",
        "label": "Rubber",
        "unit": "$/kg",
        "category": "Materials"
    },
    "Wool": {
        "fred_id": "PWOOLCUSDM",
        "label": "Wool (Coarse)",
        "unit": "$/kg",
        "category": "Materials"
    },
    
    # ===== PAPER & PULP =====
    "Paper": {
        "fred_id": "WPU0915",
        "label": "Paper & Paper Products",
        "unit": "Index",
        "category": "Paper & Packaging"
    },
    "Pulp": {
        "fred_id": "WPU0912",
        "label": "Pulp & Paper Materials",
        "unit": "Index",
        "category": "Paper & Packaging"
    },
    
    # ===== FERTILIZERS =====
    "Fertilizer": {
        "fred_id": "PFERTMTUSDM",
        "label": "Fertilizer Index",
        "unit": "Index",
        "category": "Agriculture - Inputs"
    },
    "Phosphate": {
        "fred_id": "PPHOSROCKUSDM",
        "label": "Phosphate Rock",
        "unit": "$/metric ton",
        "category": "Agriculture - Inputs"
    },
    
    # ===== RARE EARTHS & TECH MATERIALS =====
    # Note: Limited FRED data for rare earths, using proxies
    "Semiconductor_Materials": {
        "fred_id": "PCU333310333310",
        "label": "Semiconductor Materials PPI",
        "unit": "Index",
        "category": "Technology Materials"
    },
    
    # ===== REAL ESTATE INPUTS =====
    "Gypsum": {
        "fred_id": "WPU13230103",
        "label": "Gypsum Products",
        "unit": "Index",
        "category": "Construction"
    },
    "Concrete": {
        "fred_id": "PCU32732273273",
        "label": "Ready-Mix Concrete",
        "unit": "Index",
        "category": "Construction"
    },
}

# ==================== STOCK IMPACT MATRIX ====================
INDUSTRY_IMPACTS = {
    "Energy - Oil": {
        "commodities": ["Crude_Oil_WTI", "Crude_Oil_Brent"],
        "price_up_benefits": {
            "XOM": "Exxon Mobil",
            "CVX": "Chevron",
            "COP": "ConocoPhillips",
            "SLB": "Schlumberger",
            "HAL": "Halliburton",
            "OXY": "Occidental Petroleum",
            "MPC": "Marathon Petroleum",
            "VLO": "Valero Energy",
            "PSX": "Phillips 66"
        },
        "price_up_hurts": {
            "DAL": "Delta Airlines",
            "UAL": "United Airlines",
            "AAL": "American Airlines",
            "LUV": "Southwest Airlines",
            "UPS": "United Parcel Service",
            "FDX": "FedEx",
            "LYFT": "Lyft",
            "UBER": "Uber"
        },
        "sensitivity": "extreme",
        "notes": "Airlines spend 20-25% of revenue on fuel. Every $10 oil increase = ~$1B industry cost."
    },
    
    "Energy - Natural Gas": {
        "commodities": ["Natural_Gas"],
        "price_up_benefits": {
            "EQT": "EQT Corporation",
            "AR": "Antero Resources",
            "RRC": "Range Resources",
            "CNX": "CNX Resources"
        },
        "price_up_hurts": {
            "DUK": "Duke Energy (utilities)",
            "SO": "Southern Company",
            "D": "Dominion Energy",
            "DOW": "Dow Chemical",
            "LYB": "LyondellBasell"
        },
        "sensitivity": "high",
        "notes": "Natural gas is major input for electricity generation and chemical manufacturing"
    },
    
    "Metals - Steel": {
        "commodities": ["Steel_Import", "Iron_Ore"],
        "price_up_benefits": {
            "X": "United States Steel",
            "NUE": "Nucor",
            "STLD": "Steel Dynamics",
            "CLF": "Cleveland-Cliffs",
            "MT": "ArcelorMittal"
        },
        "price_up_hurts": {
            "CAT": "Caterpillar",
            "DE": "Deere & Company",
            "F": "Ford",
            "GM": "General Motors",
            "BA": "Boeing",
            "LMT": "Lockheed Martin"
        },
        "sensitivity": "high",
        "notes": "Steel is 15-20% of manufacturing costs for heavy equipment"
    },
    
    "Metals - Copper": {
        "commodities": ["Copper"],
        "price_up_benefits": {
            "FCX": "Freeport-McMoRan",
            "SCCO": "Southern Copper",
            "TECK": "Teck Resources"
        },
        "price_up_hurts": {
            "EMR": "Emerson Electric",
            "ETN": "Eaton",
            "PWR": "Quanta Services (electrical grid)",
            "TSLA": "Tesla (wiring)"
        },
        "sensitivity": "medium",
        "notes": "Copper is economic bellwether - rallies when economy strong"
    },
    
    "Metals - Aluminum": {
        "commodities": ["Aluminum"],
        "price_up_benefits": {
            "AA": "Alcoa",
            "CENX": "Century Aluminum"
        },
        "price_up_hurts": {
            "BA": "Boeing",
            "F": "Ford",
            "GM": "General Motors",
            "TSLA": "Tesla",
            "AAL": "American Airlines (aircraft)"
        },
        "sensitivity": "medium"
    },
    
    "Metals - Lithium & Battery Materials": {
        "commodities": ["Nickel"],  # Lithium not in FRED
        "price_up_benefits": {
            "ALB": "Albemarle (lithium)",
            "SQM": "Sociedad Química (lithium)",
            "LAC": "Lithium Americas"
        },
        "price_up_hurts": {
            "TSLA": "Tesla",
            "GM": "General Motors (EVs)",
            "F": "Ford (EVs)",
            "NIO": "Nio",
            "RIVN": "Rivian",
            "LCID": "Lucid"
        },
        "sensitivity": "extreme",
        "notes": "Lithium prices fell 80% in 2023, dramatically improving EV margins"
    },
    
    "Precious Metals - Gold": {
        "commodities": ["Gold"],
        "price_up_benefits": {
            "NEM": "Newmont",
            "GOLD": "Barrick Gold",
            "AEM": "Agnico Eagle",
            "GLD": "SPDR Gold ETF",
            "GDX": "Gold Miners ETF"
        },
        "price_up_hurts": {},
        "sensitivity": "high",
        "notes": "Gold rallies during uncertainty, inflation, or dollar weakness"
    },
    
    "Agriculture - Grains": {
        "commodities": ["Wheat", "Corn", "Soybeans"],
        "price_up_benefits": {
            "ADM": "Archer Daniels Midland",
            "BG": "Bunge",
            "AGCO": "AGCO (farm equipment)",
            "DE": "Deere (grain prices up = farmers buy equipment)"
        },
        "price_up_hurts": {
            "GIS": "General Mills",
            "K": "Kellanova (Kellogg)",
            "CPB": "Campbell Soup",
            "CAG": "Conagra",
            "MDLZ": "Mondelez",
            "KHC": "Kraft Heinz",
            "TSN": "Tyson (animal feed costs)"
        },
        "sensitivity": "high",
        "notes": "Wheat/corn are major inputs for packaged food companies"
    },
    
    "Agriculture - Coffee": {
        "commodities": ["Coffee"],
        "price_up_benefits": {},
        "price_up_hurts": {
            "SBUX": "Starbucks",
            "DNKN": "Dunkin' (private)",
            "JAB": "JAB Holding (private - owns Peet's, Caribou)"
        },
        "sensitivity": "medium",
        "notes": "Coffee is 10-15% of Starbucks COGS"
    },
    
    "Agriculture - Cocoa & Sugar": {
        "commodities": ["Cocoa", "Sugar"],
        "price_up_benefits": {},
        "price_up_hurts": {
            "HSY": "Hershey",
            "MDLZ": "Mondelez",
            "KO": "Coca-Cola",
            "PEP": "PepsiCo"
        },
        "sensitivity": "high",
        "notes": "Cocoa prices hit record highs in 2024, squeezing chocolate makers"
    },
    
    "Agriculture - Livestock": {
        "commodities": ["Beef", "Pork", "Chicken"],
        "price_up_benefits": {
            "TSN": "Tyson Foods",
            "HRL": "Hormel",
            "PPC": "Pilgrim's Pride"
        },
        "price_up_hurts": {
            "MCD": "McDonald's",
            "YUM": "Yum Brands (KFC, Taco Bell)",
            "QSR": "Restaurant Brands (Burger King)",
            "CMG": "Chipotle",
            "WEN": "Wendy's"
        },
        "sensitivity": "medium"
    },
    
    "Construction - Lumber": {
        "commodities": ["Lumber"],
        "price_up_benefits": {
            "WY": "Weyerhaeuser",
            "PCH": "PotlatchDeltic"
        },
        "price_up_hurts": {
            "HD": "Home Depot",
            "LOW": "Lowe's",
            "DHI": "D.R. Horton",
            "LEN": "Lennar",
            "PHM": "PulteGroup",
            "NVR": "NVR",
            "TOL": "Toll Brothers"
        },
        "sensitivity": "extreme",
        "notes": "Lumber crashed 70% in 2022 from COVID highs"
    },
    
    "Construction - Cement & Concrete": {
        "commodities": ["Cement", "Concrete"],
        "price_up_benefits": {
            "VMC": "Vulcan Materials",
            "MLM": "Martin Marietta",
            "CX": "Cemex"
        },
        "price_up_hurts": {
            "DHI": "D.R. Horton",
            "LEN": "Lennar",
            "PHM": "PulteGroup",
            "CAT": "Caterpillar (infrastructure projects)"
        },
        "sensitivity": "medium"
    },
    
    "Technology - Semiconductors": {
        "commodities": ["Semiconductor_Materials"],
        "price_up_benefits": {},
        "price_up_hurts": {
            "NVDA": "Nvidia",
            "AMD": "AMD",
            "INTC": "Intel",
            "TSM": "TSMC",
            "MU": "Micron",
            "QCOM": "Qualcomm",
            "TXN": "Texas Instruments",
            "AVGO": "Broadcom",
            "AMAT": "Applied Materials",
            "LRCX": "Lam Research"
        },
        "sensitivity": "low",
        "notes": "Silicon wafer costs are small % of total chip cost (design/R&D dominates)"
    },
    
    "Technology - Consumer Electronics": {
        "commodities": ["Copper", "Aluminum", "Gold"],
        "price_up_benefits": {},
        "price_up_hurts": {
            "AAPL": "Apple",
            "GOOG": "Google/Alphabet",
            "MSFT": "Microsoft (Xbox, Surface)",
            "DELL": "Dell",
            "HPQ": "HP",
            "SONY": "Sony"
        },
        "sensitivity": "low",
        "notes": "Consumer electronics use small amounts of precious metals"
    },
    
    "Packaging & Logistics": {
        "commodities": ["Paper", "Pulp", "Crude_Oil_WTI"],
        "price_up_benefits": {
            "PKG": "Packaging Corp",
            "IP": "International Paper",
            "WRK": "WestRock"
        },
        "price_up_hurts": {
            "AMZN": "Amazon (shipping boxes)",
            "FDX": "FedEx",
            "UPS": "UPS"
        },
        "sensitivity": "medium"
    },
    
    "Chemicals": {
        "commodities": ["Crude_Oil_WTI", "Natural_Gas", "Crude_Oil_Chemicals"],
        "price_up_benefits": {},
        "price_up_hurts": {
            "DOW": "Dow Chemical",
            "LYB": "LyondellBasell",
            "DD": "DuPont",
            "EMN": "Eastman Chemical",
            "PPG": "PPG Industries"
        },
        "sensitivity": "high",
        "notes": "Oil/gas are primary feedstocks for petrochemicals"
    },
    
    "Automotive": {
        "commodities": ["Steel_Import", "Aluminum", "Copper", "Palladium"],
        "price_up_benefits": {},
        "price_up_hurts": {
            "F": "Ford",
            "GM": "General Motors",
            "TSLA": "Tesla",
            "TM": "Toyota",
            "HMC": "Honda",
            "STLA": "Stellantis"
        },
        "sensitivity": "high",
        "notes": "Auto makers use palladium in catalytic converters"
    },
    
    "Real Estate - Homebuilders": {
        "commodities": ["Lumber", "Cement", "Concrete", "Steel_Import", "Copper"],
        "price_up_benefits": {},
        "price_up_hurts": {
            "DHI": "D.R. Horton",
            "LEN": "Lennar",
            "PHM": "PulteGroup",
            "NVR": "NVR",
            "TOL": "Toll Brothers",
            "KBH": "KB Home",
            "MTH": "Meritage Homes"
        },
        "sensitivity": "extreme",
        "notes": "Materials are 30-40% of home construction costs"
    },
    
    "Cannabis": {
        "commodities": ["Fertilizer", "Natural_Gas"],  # Electricity for indoor growing
        "price_up_benefits": {},
        "price_up_hurts": {
            "CGC": "Canopy Growth",
            "TLRY": "Tilray",
            "CRON": "Cronos",
            "ACB": "Aurora Cannabis",
            "SNDL": "SNDL",
            "CURLF": "Curaleaf",
            "GTBIF": "Green Thumb Industries"
        },
        "sensitivity": "medium",
        "notes": "Indoor cannabis cultivation is energy-intensive"
    },
    
    "Utilities": {
        "commodities": ["Natural_Gas", "Coal"],
        "price_up_benefits": {},
        "price_up_hurts": {
            "NEE": "NextEra Energy",
            "DUK": "Duke Energy",
            "SO": "Southern Company",
            "D": "Dominion Energy",
            "AEP": "American Electric Power",
            "EXC": "Exelon"
        },
        "sensitivity": "high",
        "notes": "Natural gas is primary fuel for electricity generation"
    }
}

# ==================== CATEGORY GROUPINGS ====================
CATEGORIES = {
    "Energy": ["Crude_Oil_WTI", "Crude_Oil_Brent", "Natural_Gas", "Gasoline", "Heating_Oil", "Propane"],
    "Metals": ["Copper", "Aluminum", "Iron_Ore", "Steel_Import", "Nickel", "Zinc", "Lead", "Tin"],
    "Precious Metals": ["Gold", "Silver", "Platinum", "Palladium"],
    "Agriculture - Grains": ["Wheat", "Corn", "Soybeans", "Rice", "Barley"],
    "Agriculture - Soft": ["Coffee", "Cocoa", "Sugar", "Cotton", "Orange_Juice"],
    "Agriculture - Livestock": ["Beef", "Pork", "Chicken"],
    "Agriculture - Inputs": ["Fertilizer", "Phosphate"],
    "Construction": ["Lumber", "Cement", "Gypsum", "Concrete"],
    "Chemicals": ["Crude_Oil_Chemicals", "Plastics"],
    "Materials": ["Rubber", "Wool"],
    "Paper & Packaging": ["Paper", "Pulp"],
    "Technology Materials": ["Semiconductor_Materials"]
}