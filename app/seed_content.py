"""Starting content for the service pages. Loaded once into the database; after
that everything here is edited in the admin panel (Services)."""

IMG = "/assets/img/services/"

# Services keyed by their original title so existing databases are updated in place.
# "rename" changes the title; new services have "new": True.
SERVICES = [
    {
        "match": "Cleaning Services",
        "category": "environmental",
        "description": "Post-construction, move-in, office, residential and commercial cleaning, done thoroughly and on schedule.",
        "tags": "Post-construction, Office, Residential, Commercial",
        "details": (
            "Clean spaces are healthier, safer and more pleasant to live and work in. Our trained teams bring the right "
            "equipment, products and attention to detail to every job, whether it is a one-off deep clean or an ongoing contract.\n\n"
            "We clean offices, institutions, industrial premises, homes and commercial properties, and we specialise in getting "
            "newly built and renovated spaces ready for use."
        ),
        "includes": (
            "Post-construction and renovation cleaning\nMove-in and move-out cleaning\nOffice and institutional cleaning\n"
            "Residential and estate cleaning\nCommercial and industrial premises\nFloor scrubbing, windows and glass\n"
            "One-off deep cleans or scheduled contracts"
        ),
        "sections": [
            {
                "title": "Post-Construction Cleaning",
                "body": (
                    "Post-construction cleaning is not a regular clean. When the builders leave, they leave behind more than you can see: "
                    "fine dust settles into corners, window tracks, fixtures and fittings that ordinary cleaning misses. The space may look "
                    "finished, but it isn't necessarily clean.\n\n"
                    "Regular cleaning maintains. Post-construction cleaning restores. We use the right equipment, the right techniques and "
                    "close attention to detail so the property is ready to live in, ready to work in and ready to welcome people."
                ),
                "points_title": "What we deal with",
                "points": "Fine construction dust\nPaint splashes\nCement residue\nGrout marks\nAdhesive and sticker residue\nConstruction debris",
                "image": IMG + "post-construction.jpg",
                "image_alt": "A vacuum cleaner clearing debris from a floor",
            },
            {
                "title": "Move-In & Move-Out Cleaning",
                "body": (
                    "Moving in? Start with a professionally cleaned space. We remove accumulated dirt, dust and build-up so your new home "
                    "is fresh, hygienic and ready for occupancy.\n\n"
                    "Moving out? We leave the property spotless for the landlord's inspection or the next occupant."
                ),
                "points_title": "Typical tasks",
                "points": ("Kitchen degreasing, inside cabinets and appliances\nBathroom descaling and disinfection\n"
                           "Windows, tracks and grilles\nFloors scrubbed and mopped\nDoors, switches and fittings wiped down"),
                "image": IMG + "move-in.jpg",
                "image_alt": "A spotless, freshly cleaned kitchen",
            },
            {
                "title": "Office Cleaning",
                "body": (
                    "A clean office makes a better impression and is a healthier place to work. We clean before or after working hours "
                    "so your team isn't disrupted, on a daily, weekly or custom schedule."
                ),
                "points_title": "Includes",
                "points": ("Desks, workstations and meeting rooms\nWashrooms and kitchenettes\nFloors, carpets and entrances\n"
                           "Bins emptied and relined\nHigh-touch points disinfected"),
                "image": "/assets/img/service-facility.jpg",
                "image_alt": "A cleaner mopping the floor of an office lobby",
            },
            {
                "title": "Residential & Commercial Cleaning",
                "body": (
                    "From apartments and family homes to shops, plazas and estates, we keep private and shared spaces clean and "
                    "well maintained. Estates and commercial properties can combine cleaning with our garbage collection service "
                    "in one simple contract."
                ),
                "points_title": "We clean",
                "points": ("Homes and apartments\nEstate common areas, stairways and corridors\nShops, plazas and showrooms\n"
                           "Restaurants and hospitality spaces\nWarehouses and industrial premises"),
                "image": IMG + "residential-commercial.jpg",
                "image_alt": "A gloved hand holding a spray bottle of cleaner",
            },
        ],
    },
    {
        "match": "Fumigation & Pest Control",
        "category": "environmental",
        "details": (
            "Pests spread disease, damage property and unsettle residents and staff. We provide safe, effective pest management "
            "for homes, offices, institutions, estates and commercial premises, using products and methods suited to each site.\n\n"
            "We identify the problem, treat it, and advise you on how to keep it from coming back."
        ),
        "includes": (
            "Cockroach, bedbug and ant control\nMosquito and fly control\nRodent control\nTermite treatment\n"
            "Fumigation of premises and stores\nDisinfection and sanitisation\nPreventive treatment programmes"
        ),
    },
    {
        "match": "Garbage Collection & Waste Disposal",
        "rename": "Garbage Collection & Waste Management",
        "category": "environmental",
        "description": "Scheduled garbage collection and structured, sustainable waste management systems.",
        "details": (
            "Reliable waste collection keeps estates, businesses and institutions clean and healthy. We run scheduled garbage "
            "collection and help clients set up structured, sustainable waste management systems that work every day."
        ),
        "includes": (
            "Scheduled garbage collection\nEstate and residential waste collection\nCommercial and institutional waste\n"
            "Waste segregation guidance and bin set-up\nRecycling-friendly practices\nOne-off clean-ups and debris removal"
        ),
    },
    {
        "new": True,
        "match": "Landscaping & Gardening",
        "category": "environmental",
        "description": "Design, planting and ongoing care for gardens, lawns and outdoor spaces.",
        "tags": "Landscaping, Gardening",
        "icon": "leaf",
        "accent": "green",
        "image": IMG + "landscaping-gardening.jpg",
        "image_alt": "A landscaped garden path lined with flowers and hedges",
        "details": (
            "Well-kept outdoor spaces make a lasting first impression. We design, create and maintain gardens and grounds for "
            "homes, estates, offices and institutions, so they stay green, tidy and welcoming all year round."
        ),
        "includes": (
            "Garden design and landscaping\nLawn planting, mowing and edging\nHedge trimming and tree pruning\n"
            "Flower beds and potted plants\nWatering, weeding and feeding\nGarden waste removal"
        ),
        "sections": [
            {
                "title": "Landscaping",
                "body": ("We plan and create outdoor spaces that suit the property and the coastal climate: lawns, paths, beds and "
                         "planting that look good and are easy to maintain."),
                "points_title": "Landscaping work",
                "points": "Site clearing and soil preparation\nLawn installation\nPathways and edging\nPlanting design",
                "image": IMG + "landscaping.jpg",
                "image_alt": "A freshly mown green lawn",
            },
            {
                "title": "Gardening",
                "body": ("Regular gardening keeps everything healthy and neat. We work on a weekly or monthly schedule and adjust "
                         "care through the seasons."),
                "points_title": "Gardening care",
                "points": "Mowing and edging\nWeeding and mulching\nPruning and trimming\nWatering and feeding\nGarden waste removal",
                "image": IMG + "gardening.jpg",
                "image_alt": "Raised garden beds full of healthy plants",
            },
        ],
    },
    {
        "match": "General Supplies",
        "category": "environmental",
        "details": (
            "We supply the essential goods and consumables that keep offices, institutions and facilities running, delivered "
            "on time and to specification.\n\nOrder what you need as a one-off delivery or set up a regular supply arrangement."
        ),
        "includes": (
            "Cleaning chemicals and detergents\nHygiene and washroom consumables\nJanitorial tools and equipment\n"
            "Bin liners and waste bags\nPersonal protective equipment\nOffice and institutional consumables"
        ),
    },
    {
        "new": True,
        "match": "Property Management",
        "category": "real_estate",
        "description": "Hands-on management of residential and commercial properties on behalf of owners.",
        "tags": "Residential, Commercial",
        "icon": "home",
        "accent": "purple",
        "image": IMG + "property-management.jpg",
        "image_alt": "A white residential property with palm trees and a pool",
        "details": (
            "Owning property should be rewarding, not stressful. We take care of the day-to-day running of your residential or "
            "commercial property (tenants, maintenance, rent and records) so you get steady returns and peace of mind.\n\n"
            "Because we also provide cleaning, waste management, landscaping and facilities services, we can keep your property "
            "in excellent condition through one trusted partner."
        ),
        "includes": (
            "Tenant sourcing and screening\nLease agreements and renewals\nRent collection and arrears follow-up\n"
            "Routine inspections and maintenance\nService charge management\nMonthly reports to owners"
        ),
    },
    {
        "match": "Facility Support Services",
        "rename": "Facilities Management",
        "category": "real_estate",
        "description": "Keeping buildings safe, functional and well maintained so occupants can focus on their work.",
        "tags": "Maintenance, Building services",
        "icon": "tools",
        "image": IMG + "facilities-management.jpg",
        "image_alt": "A technician in a hard hat working on an electrical installation",
        "details": (
            "Facilities management covers everything a building needs to run smoothly. We coordinate maintenance, repairs, "
            "cleaning, security and other services for commercial buildings, estates and institutions under one plan.\n\n"
            "Planned maintenance reduces breakdowns and costs, and our team responds quickly when something needs attention."
        ),
        "includes": (
            "Planned and preventive maintenance\nElectrical, plumbing and general repairs\nCleaning, hygiene and waste services\n"
            "Grounds and landscaping care\nSecurity and access coordination\nSupplier and contractor management"
        ),
    },
    {
        "new": True,
        "match": "Rent Collection",
        "category": "real_estate",
        "description": "Timely, transparent rent collection and reporting for landlords.",
        "tags": "Landlords, Reporting",
        "icon": "receipt",
        "accent": "gold",
        "image": IMG + "rent-collection.jpg",
        "image_alt": "Rent statements with a calculator and phone",
        "details": (
            "Collecting rent on time, every month, is one of the hardest parts of being a landlord. We handle invoicing, "
            "collection and follow-up for you, and give you clear statements so you always know where your income stands."
        ),
        "includes": (
            "Monthly rent invoicing\nM-Pesa and bank payment tracking\nArrears follow-up with tenants\n"
            "Receipts and tenant statements\nMonthly landlord statements\nDeposit and service charge records"
        ),
    },
    {
        "new": True,
        "match": "Commercial Leasing",
        "category": "real_estate",
        "description": "Matching businesses with the right offices, shops and commercial spaces.",
        "tags": "Offices, Retail, Warehouses",
        "icon": "store",
        "accent": "blue",
        "image": IMG + "commercial-leasing.jpg",
        "image_alt": "An empty modern office space ready to let",
        "details": (
            "Whether you own commercial property and need reliable tenants, or run a business looking for the right space, "
            "we manage the leasing process from the first viewing to the signed lease and beyond."
        ),
        "includes": (
            "Office, retail and warehouse space\nMarketing vacant commercial units\nViewings and tenant screening\n"
            "Lease negotiation and agreements\nRenewals and rent reviews\nOngoing tenant relations"
        ),
    },
    {
        "new": True,
        "match": "Buying & Selling Land",
        "category": "real_estate",
        "description": "Guidance through buying and selling land parcels, from search to transfer.",
        "tags": "Land parcels, Due diligence",
        "icon": "map",
        "accent": "green",
        "image": IMG + "land.jpg",
        "image_alt": "Open land at sunset",
        "details": (
            "Buying or selling land is a major decision. We help buyers find suitable parcels and help owners sell, guiding both "
            "through due diligence, documentation and transfer so the process is clear and secure.\n\n"
            "Buy with confidence: we help you verify ownership and documents before any money changes hands."
        ),
        "includes": (
            "Land parcels for sale\nListing and marketing land for owners\nSite visits and viewings\n"
            "Title search and due diligence support\nSale agreements and transfer guidance\nAdvice on location and value"
        ),
    },
    {
        "new": True,
        "match": "Property Valuation",
        "category": "real_estate",
        "description": "Assessing property and land value for sale, purchase, rent or financing.",
        "tags": "Property, Land",
        "icon": "scale",
        "accent": "purple",
        "image": IMG + "valuation.jpg",
        "image_alt": "A model house and keys on a desk",
        "details": (
            "Knowing what a property is worth helps you make the right decision, whether you are buying, selling, borrowing, "
            "insuring or setting rent. We arrange property and land valuations and explain the results in plain terms."
        ),
        "includes": (
            "Residential property valuation\nCommercial property valuation\nLand valuation\nRental value assessment\n"
            "Valuation for sale, purchase or financing"
        ),
    },
]

# Display order after the update; services added by the owner keep their place after these.
ORDER = [
    "Cleaning Services", "Fumigation & Pest Control", "Garbage Collection & Waste Management", "Landscaping & Gardening",
    "General Supplies", "Property Management", "Facilities Management", "Rent Collection", "Commercial Leasing",
    "Buying & Selling Land", "Property Valuation",
]

NEW_SLIDE = ("Real Estate Services", "/assets/img/hero-realestate.jpg", "/assets/img/hero-realestate-960.jpg")
