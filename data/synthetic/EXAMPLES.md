# Synthetic data examples

Two cases per task from `data/synthetic/validated/`. Gold products are in `reward`; only `query` is LLM-written. All prices are PHP.


## product (500 cases)

### Example 1

**Query**

> Find a fan blade for an electric motor, categorized as an electric motor fan, priced between PHP 83 and PHP 141.

**Gold reward / meta / voucher**

```json
{
  "reward": {
    "product_id": "3016527958",
    "title": [
      "High Temperature Resistant Plastic Back Fan Blade for Three Phase Motor Y Series Electric Motor Fan Leaf from China Mainland"
    ],
    "attributes": [
      {
        "component_type": [
          "electric motor fan"
        ]
      }
    ],
    "price": [
      {
        "between": [
          83,
          141
        ]
      }
    ]
  },
  "meta": {
    "group": "3016527958",
    "shop_ids": [
      "1689641"
    ],
    "task": "product"
  }
}
```

### Example 2

**Query**

> Find an OMG hair color shampoo in brown, 400ml, with color protection, free shipping, and a price between PHP 169 and PHP 257.

**Gold reward / meta / voucher**

```json
{
  "reward": {
    "product_id": "4449752209",
    "title": [
      "Omg Instant Hair Color Shampoo 400ML ( Black / Brown )"
    ],
    "sku_options": [
      {
        "volume": "brown 400ml"
      }
    ],
    "attributes": [
      {
        "concerns_hair_care": [
          "color protection"
        ]
      },
      {
        "brand": [
          "omg"
        ]
      }
    ],
    "service": [
      "freeShipping"
    ],
    "price": [
      {
        "between": [
          169,
          257
        ]
      }
    ]
  },
  "meta": {
    "group": "4449752209",
    "shop_ids": [
      "1544850"
    ],
    "task": "product"
  }
}
```


## shop (511 cases)

### Example 1

**Query**

> Find a shop that sells both a milk soap for sensitive skin with brightening benefits, sold as one piece, premium quality, standard size, and hypoallergenic ingredients, and a pink whipped scrub with brightening benefits, standard size, and alpha arbutin.

**Gold reward / meta / voucher**

```json
{
  "reward": [
    {
      "product_id": "2612977656",
      "title": [
        "Sereese beauty whitening milk soap"
      ],
      "attributes": [
        {
          "skin_type": [
            "sensitive"
          ]
        },
        {
          "body_benefits": [
            "whitening"
          ]
        },
        {
          "units_hb": [
            "single item"
          ]
        },
        {
          "brand_classification": [
            "premium"
          ]
        },
        {
          "travel_size": [
            "regular size"
          ]
        },
        {
          "ingredient_preference": [
            "hypo-allergenic"
          ]
        }
      ]
    },
    {
      "product_id": "3223420292",
      "title": [
        "SEREESE BEAUTY MILKY BOOST INTENSE WHITENING WHIPPED SCRUB"
      ],
      "sku_options": [
        {
          "color_family": "pink"
        }
      ],
      "attributes": [
        {
          "body_benefits": [
            "whitening"
          ]
        },
        {
          "travel_size": [
            "regular size"
          ]
        },
        {
          "ingredient_preference": [
            "alpha arbutin"
          ]
        }
      ]
    }
  ],
  "meta": {
    "group": "533296",
    "shop_ids": [
      "533296"
    ],
    "task": "shop"
  }
}
```

### Example 2

**Query**

> Find one shop that sells all four of these shorts: 1) size XL with a navy blue/gray colorway; 2) intended for training and priced above PHP 237; 3) size S and designed for training; 4) size XS, beige, intended for cycling, currently on flash sale, and priced above PHP 207.

**Gold reward / meta / voucher**

```json
{
  "reward": [
    {
      "product_id": "5058670199",
      "title": [
        "✔  Boomslang MAMBA PRO Series  MTB Shorts Shades of Navy Blue/ Gray"
      ],
      "sku_options": [
        {
          "size": "int:xl",
          "color family": "navy blue/gray"
        }
      ]
    },
    {
      "product_id": "5058374927",
      "title": [
        "✔ Allstar Men DriCool™ Running Shorts"
      ],
      "attributes": [
        {
          "activity_type": [
            "training"
          ]
        }
      ],
      "price": [
        {
          "greater than": [
            237,
            null
          ]
        }
      ]
    },
    {
      "product_id": "5058685198",
      "title": [
        "✔ Armor On - Mens Dri-Fit WASHINGTON Printed Sportswear Training Shorts"
      ],
      "sku_options": [
        {
          "size": "int:s"
        }
      ],
      "attributes": [
        {
          "activity_type": [
            "training"
          ]
        }
      ]
    },
    {
      "product_id": "5058685172",
      "title": [
        "✔ Extreme Assault Trigger 2 MTB Shorts Khaki"
      ],
      "sku_options": [
        {
          "size": "int:xs",
          "color family": "beige"
        }
      ],
      "attributes": [
        {
          "activity_type": [
            "cycling"
          ]
        }
      ],
      "service": [
        "flashsale"
      ],
      "price": [
        {
          "greater than": [
            207,
            null
          ]
        }
      ]
    }
  ],
  "meta": {
    "group": "5733689",
    "shop_ids": [
      "5733689"
    ],
    "task": "shop"
  }
}
```


## voucher (471 cases)

### Example 1

**Query**

> Find a carbon-fiber road bike, and an Xpanse gaming chair with the model name "gaming chair" in the X-Bomb Pro Chair style.
> 
> My budget is only PHP `33043`, but I have a voucher with the following rules:
> 1. The voucher applies to all products.
> 2. It is valid only when the total price of the products exceeds PHP `11630`.
> 3. It provides a fixed discount of PHP `4640`.

**Gold reward / meta / voucher**

```json
{
  "reward": [
    {
      "product_id": "4543845450",
      "title": [
        "wheeltop eds tx disc brake road bicycle wireless electronic Derailleur Groupset carbon fiber 7s-13s"
      ],
      "attributes": [
        {
          "material": [
            "carbon fiber"
          ]
        }
      ]
    },
    {
      "product_id": "5130200699",
      "title": [
        "【30 Day Free Trial】Xpanse X-Bomb Skull Gaming Chair With Foot Rest Office Computer Chair Ergonomic Chair"
      ],
      "sku_options": [
        {
          "style": "x-bomb pro chair"
        }
      ],
      "attributes": [
        {
          "brand": [
            "xpanse"
          ]
        },
        {
          "model": [
            "gaming chair"
          ]
        }
      ]
    }
  ],
  "meta": {
    "group": "1686079",
    "shop_ids": [
      "1686079",
      "5153538"
    ],
    "task": "voucher"
  },
  "voucher": {
    "discount_type": "fixed",
    "face_value": 4640,
    "discount": null,
    "cap": null,
    "voucher_type": "platform",
    "threshold": 11630,
    "price_after_voucher": 32800.68,
    "budget": 33043
  }
}
```

### Example 2

**Query**

> Find an OEM phone case compatible with Huawei, plus men's running shoes in EU size 44 from the grey color family.
> 
> My budget is only PHP `3548`, but I have a voucher with the following rules:
> 1. The voucher only applies to the products from the same shop.
> 2. It is valid only when the total price of the products exceeds PHP `807`.
> 3. It provides a percentage discount of `50%` with a cap of PHP `499`.

**Gold reward / meta / voucher**

```json
{
  "reward": [
    {
      "product_id": "4647878461",
      "title": [
        "＜918＞UAG Plasma Case for Huawei Mate 30 Pro / Mate 20X / Mate 20 Pro / Mate 20  strong durable but lightweight."
      ],
      "attributes": [
        {
          "brand_compatibility": [
            "huawei"
          ]
        },
        {
          "brand": [
            "oem"
          ]
        }
      ]
    },
    {
      "product_id": "4989780246",
      "title": [
        "《317》Cameljeans Wind Speed ​​2.0 Sports Shoes Mens New Outdoor Running Shoes All Terrain Jogging Shoes"
      ],
      "sku_options": [
        {
          "size": "eu:44",
          "color family": "grey"
        }
      ]
    }
  ],
  "meta": {
    "group": "939572",
    "shop_ids": [
      "939572"
    ],
    "task": "voucher"
  },
  "voucher": {
    "discount_type": "percentage",
    "face_value": null,
    "discount": 0.5,
    "cap": 499,
    "voucher_type": "shop",
    "threshold": 807,
    "price_after_voucher": 3357.8999999999996,
    "budget": 3548
  }
}
```


## compound (419 cases)

### Example 1

**Query**

> Find one shop where I can buy all four products and use the same-shop voucher: (1) a Toocki USB Type-C cable in the “c to ios 20w” color family; (2) a USB cable with USB2: 0-480mbps data transfer speed; (3) a Toocki USB charger in the EU-white option, sold through a LazMall official store; and (4) a Lightning audio adapter cable with USB2: 0-480mbps data transfer speed.
> 
> My budget is only PHP `480`, but I have a voucher with the following rules:
> 1. The voucher only applies to the products from the same shop.
> 2. It is valid only when the total price of the products exceeds PHP `491`.
> 3. It provides a fixed discount of PHP `79`.

**Gold reward / meta / voucher**

```json
{
  "reward": [
    {
      "product_id": "4275073048",
      "title": [
        "Toocki 0.25M USB Type C to Type-C Usb ios Cable Fast Charging Data Cord Short Portable Mini Cable Charge for Samsung Iphone Xiaomi"
      ],
      "sku_options": [
        {
          "color_family": "c to ios 20w"
        }
      ],
      "attributes": [
        {
          "brand": [
            "toocki"
          ]
        }
      ]
    },
    {
      "product_id": "4444183312",
      "title": [
        "Toocki 0.25m Portable Ultra Short USB Fast Charging Cable For Power Bank MP3 MP4 Camera Xiaomi Oneplus Phone Type C Micro Cord"
      ],
      "attributes": [
        {
          "data_trans_speed": [
            "usb2: 0-480mbps"
          ]
        }
      ]
    },
    {
      "product_id": "3950495489",
      "title": [
        "Toocki 100W USB Charger PD Quick Charge 5.0 USB Type C Charger Fast Charging Adapter For iPhone 14 13 Pro Max Samsung Xiaomi Tablet"
      ],
      "sku_options": [
        {
          "variation": "eu-white"
        }
      ],
      "attributes": [
        {
          "brand": [
            "toocki"
          ]
        }
      ],
      "service": [
        "official"
      ]
    },
    {
      "product_id": "4252393853",
      "title": [
        "Toocki Lightning To 3 5 Mm Jack Aux Cable Adapter for Iphone 12 13 14 Pro Adapter Headphone Connector Audio Splitter Iphone Accessories"
      ],
      "attributes": [
        {
          "data_trans_speed": [
            "usb2: 0-480mbps"
          ]
        }
      ]
    }
  ],
  "meta": {
    "group": "261522",
    "shop_ids": [
      "261522"
    ],
    "task": "compound"
  },
  "voucher": {
    "discount_type": "fixed",
    "face_value": 79,
    "discount": null,
    "cap": null,
    "voucher_type": "shop",
    "threshold": 491,
    "price_after_voucher": 468.48,
    "budget": 480
  }
}
```

### Example 2

**Query**

> Find one shop that sells all four products: a Clas coin organizer made of plastic, suitable for everyone, with box-style storage; a multipurpose box classified as a desk organizer; a white storage organizer made from polypropylene (PP), classified as a desk organizer and eligible for free shipping; and a key chain organizer with star key tags and cash on delivery. The same shop must offer all items so one shop voucher can be used.
> 
> My budget is only PHP `913`, but I have a voucher with the following rules:
> 1. The voucher only applies to the products from the same shop.
> 2. It is valid only when the total price of the products exceeds PHP `1375`.
> 3. It provides a percentage discount of `43%` with a cap of PHP `1324`.

**Gold reward / meta / voucher**

```json
{
  "reward": [
    {
      "product_id": "4209922481",
      "title": [
        "Clas Coin Tube Coin Organizer for 5 10 20 1 peso coins 4 pcs per pack"
      ],
      "attributes": [
        {
          "nursery_furniture_material": [
            "plastic"
          ]
        },
        {
          "recommended_gender": [
            "unisex"
          ]
        },
        {
          "storage_type": [
            "boxes"
          ]
        },
        {
          "brand": [
            "clas"
          ]
        }
      ]
    },
    {
      "product_id": "4339201912",
      "title": [
        "Fortune Box 4 Partition MultiPurpose Box for Cash Jewelries Office and Hardware Tools Organizer"
      ],
      "attributes": [
        {
          "stationery_deskorg_type": [
            "desk organizers"
          ]
        }
      ]
    },
    {
      "product_id": "3353250416",
      "title": [
        "Clas Stackie Loaded Drawer 5 Layer Storage Organizer Fit up to Long Bond Paper"
      ],
      "sku_options": [
        {
          "variation3": "white"
        }
      ],
      "attributes": [
        {
          "material": [
            "polypropylene (pp)"
          ]
        },
        {
          "stationery_deskorg_type": [
            "desk organizers"
          ]
        }
      ],
      "service": [
        "freeShipping"
      ]
    },
    {
      "product_id": "4596860371",
      "title": [
        "CLAS Key Chain Organizer With Split Ring Label Window | Key Tags to name your Keys and Organize"
      ],
      "sku_options": [
        {
          "key tags": "star"
        }
      ],
      "service": [
        "COD"
      ]
    }
  ],
  "meta": {
    "group": "1268586",
    "shop_ids": [
      "1268586"
    ],
    "task": "compound"
  },
  "voucher": {
    "discount_type": "percentage",
    "face_value": null,
    "discount": 0.43,
    "cap": 1324,
    "voucher_type": "shop",
    "threshold": 1375,
    "price_after_voucher": 891.4800000000001,
    "budget": 913
  }
}
```
