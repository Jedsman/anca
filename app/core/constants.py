# Constants and Mock Data for eBay Sniper

MOCK_LISTINGS = [
    {
        "itemId": "123456789",
        "title": "Vintage Sony Walkman WM-2 Cassette Player - Untested",
        "viewItemURL": "http://ebay.com/item/123456789",
        "price": 45.00,
        "currency": "USD",
        "bidCount": 1,
        "endTime": "2024-12-25T12:00:00Z",
        "listingType": "Auction",
        "shipping_cost": 10.00,
        "condition": "For parts or not working"
    },
    {
        "itemId": "987654321",
        "title": "Canon AE-1 Program Camera Body Only working",
        "viewItemURL": "http://ebay.com/item/987654321",
        "price": 60.00,
        "currency": "USD",
        "bidCount": 0,
        "endTime": "2024-12-25T13:00:00Z",
        "listingType": "Auction",
        "shipping_cost": 15.00,
        "condition": "Used"
    }
]

MOCK_COMPLETED = [
    {
        "itemId": "111111111",
        "title": "Vintage Sony Walkman WM-2 Cassette Player Refurbished",
        "sold_price": 250.00,
        "currency": "USD",
        "condition": "Seller refurbished",
        "shipping_cost": 10.00
    },
    {
        "itemId": "222222222",
        "title": "Sony Walkman WM-2 good condition",
        "sold_price": 180.00,
        "currency": "USD",
        "condition": "Used",
        "shipping_cost": 10.00
    },
    {
        "itemId": "333333333",
        "title": "Canon AE-1 Program Body",
        "sold_price": 120.00,
        "currency": "USD",
        "condition": "Used",
        "shipping_cost": 15.00
    }
]
