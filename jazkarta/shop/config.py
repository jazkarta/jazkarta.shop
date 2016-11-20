import os

# note: if the JAZKARTA_SHOP_PRODUCTION exists in the environment 
# the system considers itself to be in PRODUCTION mode, setting 
# JAZKARTA_SHOP_PRODUCTION=False does not mean that one is now in DEVELOPMENT 
# mode, one is still in PRODUCTION - instead unset the JAZKARTA_SHOP_PRODUCTION
# variable to return to DEVELOPMENT mode
IN_PRODUCTION = os.environ.get('JAZKARTA_SHOP_PRODUCTION', False)

STORAGE_KEY = '_jaz_shop'

SHIPPING_ZONES = [
    u'Alaska',
    u'Canada',
    u'East',
    u'Hawaii',
    u'International',
    u'Midwest',
    u'US',
    u'West',
]
WEST = {
    'AZ', 'CA', 'CO', 'ID', 'MT', 'NV', 'NM', 'OR', 'UT', 'WY'
}
MIDWEST = {
    'AL', 'AR', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'MI', 'MN', 'MS',
    'MO', 'NE', 'ND', 'OH', 'OK', 'SD', 'TN', 'TX', 'WI',
}
EAST = {
    'CT', 'DE', 'FL', 'GA', 'ME', 'MD', 'MA', 'NH', 'NJ', 'NY', 'NC',
    'PA', 'RI', 'SC', 'VT', 'VA', 'WV'
}


# Countries for looking up shipping.
# (USPS country name, UPS country code)
SHIPPING_COUNTRIES = (
    ("United States", "US"),
    ("Canada", "CA"),
    ("Afghanistan", "AF"),
    ("Aland Island (Finland)", "AX"),
    ("Albania", "AL"),
    ("Algeria", "DZ"),
    ("American Samoa", "AS"),
    ("Andorra", "AD"),
    ("Angola", "AO"),
    ("Anguilla", "AI"),
    ("Antigua and Barbuda", "AG"),
    ("Argentina", "AR"),
    ("Armenia", "AR"),
    ("Aruba", "AW"),
    ("Australia", "AU"),
    ("Austria", "AT"),
    ("Azerbaijan", "AZ"),
    ("Bahamas", "BS"),
    ("Bahrain", "BH"),
    ("Bangladesh", "BD"),
    ("Barbados", "BB"),
    ("Belarus", "BY"),
    ("Belgium", "BE"),
    ("Belize", "BZ"),
    ("Benin", "BJ"),
    ("Bermuda", "BM"),
    ("Bhutan", "BT"),
    ("Bolivia", "BO"),
    ("Bonaire (Curacao)", "BQ"),
    ("Bosnia-Herzegovina", "BA"),
    ("Botswana", "BW"),
    ("Brazil", "BR"),
    ("British Virgin Islands", ""),
    ("Brunei Darussalam", "BN"),
    ("Bulgaria", "BG"),
    ("Burkina Faso", "BF"),
    ("Burundi", "BI"),
    ("Cambodia", "KH"),
    ("Cameroon", "CM"),
    ("Cape Verde", "CV"),
    ("Cayman Islands", "KY"),
    ("Central African Republic", "CF"),
    ("Chad", "TD"),
    ("Chile", "CL"),
    ("China", "CN"),
    ("Christmas Island (Australia)", "CX"),
    ("Christmas Island (Kiribati)", "CX"),
    ("Cocos Island (Australia)", "CC"),
    ("Colombia", "CO"),
    ("Comoros", "KM"),
    ("Congo, Democratic Republic of the", "CD"),
    ("Congo, Republic of the", "CG"),
    ("Cook Islands (New Zealand)", "CK"),
    ("Costa Rica", "CR"),
    ("Cote d Ivoire", "CI"),
    ("Croatia", "HR"),
    ("Cuba", "CU"),
    ("Curacao", "CW"),
    ("Cyprus", "CY"),
    ("Czech Republic", "CZ"),
    ("Denmark", "DK"),
    ("Djibouti", "DJ"),
    ("Dominica", "DM"),
    ("Dominican Republic", "DO"),
    ("Ecuador", "EC"),
    ("Egypt", "EG"),
    ("El Salvador", "SV"),
    ("Equatorial Guinea", "GQ"),
    ("Eritrea", "ER"),
    ("Estonia", "EE"),
    ("Ethiopia", "ET"),
    ("Falkland Islands", "FK"),
    ("Faroe Islands", "FO"),
    ("Fiji", "FJ"),
    ("Finland", "FI"),
    ("France", "FR"),
    ("French Guiana", "GF"),
    ("French Polynesia", "PF"),
    ("Gabon", "GA"),
    ("Gambia", "GM"),
    ("Georgia, Republic of", "GE"),
    ("Germany", "DE"),
    ("Ghana", "GH"),
    ("Gibraltar", "GI"),
    ("Greece", "GR"),
    ("Greenland", "GL"),
    ("Grenada", "GD"),
    ("Guadeloupe", "GP"),
    ("Guatemala", "GT"),
    ("Guernsey (Channel Islands) (Great Britain and Northern Ireland)", "GG"),
    ("Guinea", "GN"),
    ("Guinea-Bissau", "GW"),
    ("Guyana", "GY"),
    ("Haiti", "HT"),
    ("Honduras", "HN"),
    ("Hong Kong", "HK"),
    ("Hungary", "HU"),
    ("Iceland", "IS"),
    ("India", "IN"),
    ("Indonesia", "ID"),
    ("Iran", "IR"),
    ("Iraq", "IQ"),
    ("Ireland", "IE"),
    ("Isle of Man (Great Britain and Northern Ireland)", "IM"),
    ("Israel", "IL"),
    ("Italy", "IT"),
    ("Jamaica", "JM"),
    ("Japan", "JP"),
    ("Jersey (Channel Islands) (Great Britain and Northern Ireland)", "JE"),
    ("Jordan", "JO"),
    ("Kazakhstan", "KZ"),
    ("Keeling Islands (Australia)", "CC"),
    ("Kenya", "KE"),
    ("Kiribati", "KI"),
    ("Kosovo, Republic of", ""),
    ("Kuwait", "KW"),
    ("Kyrgyzstan", "KG"),
    ("Laos", "LA"),
    ("Latvia", "LV"),
    ("Lebanon", "LB"),
    ("Lesotho", "LS"),
    ("Liberia", "LR"),
    ("Libya", "LY"),
    ("Liechtenstein", "LI"),
    ("Lithuania", "LT"),
    ("Luxembourg", "LU"),
    ("Macao", "MO"),
    ("Macedonia, Republic of", "MK"),
    ("Madagascar", "MG"),
    ("Malawi", "MW"),
    ("Malaysia", "MY"),
    ("Maldives", "MV"),
    ("Mali", "ML"),
    ("Malta", "MT"),
    ("Marshall Islands, Republic of the", "MH"),
    ("Martinique", "MQ"),
    ("Mauritania", "MR"),
    ("Mauritius", "MU"),
    ("Mexico", "MX"),
    ("Micronesia, Federated States of", "FM"),
    ("Moldova", "MD"),
    ("Monaco (France)", "MC"),
    ("Mongolia", "MN"),
    ("Montenegro", "ME"),
    ("Montserrat", "MS"),
    ("Morocco", "MA"),
    ("Mozambique", "MZ"),
    ("Myanmar (Burma)", "MM"),
    ("Namibia", "NA"),
    ("Nauru", "NR"),
    ("Nepal", "NP"),
    ("Netherlands", "NL"),
    ("New Caledonia", "NC"),
    ("New Zealand", "NZ"),
    ("Nicaragua", "NI"),
    ("Niger", "NE"),
    ("Nigeria", "NG"),
    ("Norfolk Island (Australia)", "NF"),
    ("North Korea (Korea, Democratic People's Republic of)", "KP"),
    ("Norway", "NO"),
    ("Oman", "OM"),
    ("Pakistan", "PK"),
    ("Palau", "PW"),
    ("Panama", "PA"),
    ("Papua New Guinea", "PG"),
    ("Paraguay", "PY"),
    ("Peru", "PE"),
    ("Philippines", "PH"),
    ("Pitcairn Island", "PN"),
    ("Poland", "PL"),
    ("Portugal", "PT"),
    ("Qatar", "QA"),
    ("Reunion", "RE"),
    ("Romania", "RO"),
    ("Russia", "RU"),
    ("Rwanda", "RW"),
    ("Saint Christopher and Nevis", "KN"),
    ("Saint Helena", "SH"),
    ("Saint Lucia", "LC"),
    ("Saint Pierre and Miquelon", "PM"),
    ("Saint Vincent and the Grenadines", "VC"),
    ("San Marino", "SM"),
    ("Sao Tome and Principe", "ST"),
    ("Saudi Arabia", "SA"),
    ("Senegal", "SN"),
    ("Serbia, Republic of", "RS"),
    ("Seychelles", "SC"),
    ("Sierra Leone", "SL"),
    ("Singapore", "SG"),
    ("Sint Maarten (Dutch)", "SX"),
    ("Slovak Republic (Slovakia)", "SK"),
    ("Slovenia", "SI"),
    ("Solomon Islands", "SB"),
    ("Somalia", "SO"),
    ("South Africa", "ZA"),
    ("South Georgia (Falkland Islands)", "GS"),
    ("South Korea (Korea, Republic of)", "KR"),
    ("Spain", "ES"),
    ("Sri Lanka", "LK"),
    ("Sudan", "SD"),
    ("Suriname", "SR"),
    ("Swaziland", "SZ"),
    ("Sweden", "SE"),
    ("Switzerland", "CH"),
    ("Syrian Arab Republic (Syria)", "SY"),
    ("Taiwan", "TW"),
    ("Tajikistan", "TJ"),
    ("Tanzania", "TZ"),
    ("Thailand", "TH"),
    ("Timor-Leste, Democratic Republic of", "TL"),
    ("Togo", "TG"),
    ("Tokelau (Western Samoa)", "TK"),
    ("Tonga", "TO"),
    ("Trinidad and Tobago", "TT"),
    ("Tunisia", "TN"),
    ("Turkey", "TR"),
    ("Turkmenistan", "TM"),
    ("Turks and Caicos Islands", "TC"),
    ("Tuvalu", "TV"),
    ("Uganda", "UG"),
    ("Ukraine", "UA"),
    ("United Arab Emirates", "AE"),
    ("United Kingdom (Great Britain and Northern Ireland)", "GB"),
    ("Uruguay", "UY"),
    ("Uzbekistan", "UZ"),
    ("Vanuatu", "VU"),
    ("Vatican City", "VA"),
    ("Venezuela", "VE"),
    ("Vietnam", "VN"),
    ("Virgin Islands (British)", "VG"),
    ("Wallis and Futuna Islands", "WF"),
    ("Yemen", "YE"),
    ("Zambia", "ZM"),
    ("Zimbabwe", "ZW"),
)
