["I need some help", {
    "I don't know what to make": ["Are you making this Gift for a specific Contractor?", {
        "Yes": ["Are you having trouble coming up with flavorful Gifts or useful Gifts?", {
            "Flavorful": ["#ps2-flavorful-gifts"],
            "Useful": ["Is this Contractor Novice or Seasoned?", {
                "Novice": ["#ps2-novice-gift-advice"],
                "Seasoned": ["#ps2-seasoned-gift-advice"]
            }]
        }],
        "No": ["Well then why are you making a Gift?", {
            "Just trying out this system": ["#ps2-trying-out-system"],
            "I'm making a Gift for an NPC": ["#ps2-npc-gifts"]
            }]
        }]},
    "I'm having trouble making what I want": ["#ps2-limitations-block", {

    }],
    "I'm curious about this Gift creator": ["What are you curious about?", {
        "Its rules and structure": ["#ps2-gift-rules"],
        "Its role in The Contract": ["#ps2-contract-gifts"],
        "Its design and philosophy": ["#ps2-gift-philosophy"]
    }]
}];