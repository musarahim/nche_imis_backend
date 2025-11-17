import json
import re

import requests
from common.models import County, District, Parish, SubCounty, Village

counties_list = []
uri='https://ppdev.cml.ug/'
    
districts =[
  {
    "value": "98",
    "text": "ABIM"
  },
  {
    "value": "68",
    "text": "ADJUMANI"
  },
  {
    "value": "23",
    "text": "AGAGO"
  },
  {
    "value": "116",
    "text": "ALEBTONG"
  },
  {
    "value": "85",
    "text": "AMOLATAR"
  },
  {
    "value": "109",
    "text": "AMUDAT"
  },
  {
    "value": "86",
    "text": "AMURIA"
  },
  {
    "value": "99",
    "text": "AMURU"
  },
  {
    "value": "1",
    "text": "APAC"
  },
  {
    "value": "2",
    "text": "ARUA"
  },
  {
    "value": "100",
    "text": "BUDAKA"
  },
  {
    "value": "106",
    "text": "BUDUDA"
  },
  {
    "value": "69",
    "text": "BUGIRI"
  },
  {
    "value": "36",
    "text": "BUGWERI"
  },
  {
    "value": "20",
    "text": "BUHWEJU"
  },
  {
    "value": "110",
    "text": "BUIKWE"
  },
  {
    "value": "107",
    "text": "BUKEDEA"
  },
  {
    "value": "126",
    "text": "BUKOMANSIMBI"
  },
  {
    "value": "87",
    "text": "BUKWO"
  },
  {
    "value": "117",
    "text": "BULAMBULI"
  },
  {
    "value": "101",
    "text": "BULIISA"
  },
  {
    "value": "3",
    "text": "BUNDIBUGYO"
  },
  {
    "value": "29",
    "text": "BUNYANGABU"
  },
  {
    "value": "4",
    "text": "BUSHENYI"
  },
  {
    "value": "70",
    "text": "BUSIA"
  },
  {
    "value": "88",
    "text": "BUTALEJA"
  },
  {
    "value": "127",
    "text": "BUTAMBALA"
  },
  {
    "value": "30",
    "text": "BUTEBO"
  },
  {
    "value": "118",
    "text": "BUVUMA"
  },
  {
    "value": "111",
    "text": "BUYENDE"
  },
  {
    "value": "102",
    "text": "DOKOLO"
  },
  {
    "value": "119",
    "text": "GOMBA"
  },
  {
    "value": "5",
    "text": "GULU"
  },
  {
    "value": "6",
    "text": "HOIMA"
  },
  {
    "value": "89",
    "text": "IBANDA"
  },
  {
    "value": "7",
    "text": "IGANGA"
  },
  {
    "value": "90",
    "text": "ISINGIRO"
  },
  {
    "value": "8",
    "text": "JINJA"
  },
  {
    "value": "91",
    "text": "KAABONG"
  },
  {
    "value": "9",
    "text": "KABALE"
  },
  {
    "value": "10",
    "text": "KABAROLE"
  },
  {
    "value": "82",
    "text": "KABERAMAIDO"
  },
  {
    "value": "25",
    "text": "KAGADI"
  },
  {
    "value": "26",
    "text": "KAKUMIRO"
  },
  {
    "value": "129",
    "text": "KALAKI"
  },
  {
    "value": "21",
    "text": "KALANGALA"
  },
  {
    "value": "92",
    "text": "KALIRO"
  },
  {
    "value": "11",
    "text": "KALUNGU"
  },
  {
    "value": "32",
    "text": "KAMPALA"
  },
  {
    "value": "42",
    "text": "KAMULI"
  },
  {
    "value": "74",
    "text": "KAMWENGE"
  },
  {
    "value": "83",
    "text": "KANUNGU"
  },
  {
    "value": "43",
    "text": "KAPCHORWA"
  },
  {
    "value": "37",
    "text": "KAPELEBYONG"
  },
  {
    "value": "130",
    "text": "KARENGA"
  },
  {
    "value": "38",
    "text": "KASANDA"
  },
  {
    "value": "44",
    "text": "KASESE"
  },
  {
    "value": "71",
    "text": "KATAKWI"
  },
  {
    "value": "75",
    "text": "KAYUNGA"
  },
  {
    "value": "132",
    "text": "KAZO"
  },
  {
    "value": "45",
    "text": "KIBAALE"
  },
  {
    "value": "46",
    "text": "KIBOGA"
  },
  {
    "value": "13",
    "text": "KIBUKU"
  },
  {
    "value": "39",
    "text": "KIKUUBE"
  },
  {
    "value": "93",
    "text": "KIRUHURA"
  },
  {
    "value": "120",
    "text": "KIRYANDONGO"
  },
  {
    "value": "47",
    "text": "KISORO"
  },
  {
    "value": "133",
    "text": "KITAGWENDA"
  },
  {
    "value": "48",
    "text": "KITGUM"
  },
  {
    "value": "94",
    "text": "KOBOKO"
  },
  {
    "value": "14",
    "text": "KOLE"
  },
  {
    "value": "49",
    "text": "KOTIDO"
  },
  {
    "value": "50",
    "text": "KUMI"
  },
  {
    "value": "40",
    "text": "KWANIA"
  },
  {
    "value": "15",
    "text": "KWEEN"
  },
  {
    "value": "121",
    "text": "KYANKWANZI"
  },
  {
    "value": "112",
    "text": "KYEGEGWA"
  },
  {
    "value": "76",
    "text": "KYENJOJO"
  },
  {
    "value": "31",
    "text": "KYOTERA"
  },
  {
    "value": "113",
    "text": "LAMWO"
  },
  {
    "value": "51",
    "text": "LIRA"
  },
  {
    "value": "122",
    "text": "LUUKA"
  },
  {
    "value": "52",
    "text": "LUWEERO"
  },
  {
    "value": "16",
    "text": "LWENGO"
  },
  {
    "value": "108",
    "text": "LYANTONDE"
  },
  {
    "value": "134",
    "text": "MADI-OKOLLO"
  },
  {
    "value": "95",
    "text": "MANAFWA"
  },
  {
    "value": "105",
    "text": "MARACHA"
  },
  {
    "value": "53",
    "text": "MASAKA"
  },
  {
    "value": "54",
    "text": "MASINDI"
  },
  {
    "value": "77",
    "text": "MAYUGE"
  },
  {
    "value": "55",
    "text": "MBALE"
  },
  {
    "value": "56",
    "text": "MBARARA"
  },
  {
    "value": "17",
    "text": "MITOOMA"
  },
  {
    "value": "96",
    "text": "MITYANA"
  },
  {
    "value": "57",
    "text": "MOROTO"
  },
  {
    "value": "135",
    "text": "MOYO"
  },
  {
    "value": "58",
    "text": "MPIGI"
  },
  {
    "value": "59",
    "text": "MUBENDE"
  },
  {
    "value": "60",
    "text": "MUKONO"
  },
  {
    "value": "41",
    "text": "NABILATUK"
  },
  {
    "value": "84",
    "text": "NAKAPIRIPIRIT"
  },
  {
    "value": "97",
    "text": "NAKASEKE"
  },
  {
    "value": "72",
    "text": "NAKASONGOLA"
  },
  {
    "value": "123",
    "text": "NAMAYINGO"
  },
  {
    "value": "33",
    "text": "NAMISINDWA"
  },
  {
    "value": "103",
    "text": "NAMUTUMBA"
  },
  {
    "value": "18",
    "text": "NAPAK"
  },
  {
    "value": "61",
    "text": "NEBBI"
  },
  {
    "value": "19",
    "text": "NGORA"
  },
  {
    "value": "124",
    "text": "NTOROKO"
  },
  {
    "value": "62",
    "text": "NTUNGAMO"
  },
  {
    "value": "22",
    "text": "NWOYA"
  },
  {
    "value": "136",
    "text": "OBONGI"
  },
  {
    "value": "27",
    "text": "OMORO"
  },
  {
    "value": "114",
    "text": "OTUKE"
  },
  {
    "value": "104",
    "text": "OYAM"
  },
  {
    "value": "78",
    "text": "PADER"
  },
  {
    "value": "34",
    "text": "PAKWACH"
  },
  {
    "value": "63",
    "text": "PALLISA"
  },
  {
    "value": "64",
    "text": "RAKAI"
  },
  {
    "value": "28",
    "text": "RUBANDA"
  },
  {
    "value": "24",
    "text": "RUBIRIZI"
  },
  {
    "value": "35",
    "text": "RUKIGA"
  },
  {
    "value": "65",
    "text": "RUKUNGIRI"
  },
  {
    "value": "137",
    "text": "RWAMPARA"
  },
  {
    "value": "125",
    "text": "SERERE"
  },
  {
    "value": "12",
    "text": "SHEEMA"
  },
  {
    "value": "79",
    "text": "SIRONKO"
  },
  {
    "value": "66",
    "text": "SOROTI"
  },
  {
    "value": "73",
    "text": "SSEMBABULE"
  },
  {
    "value": "67",
    "text": "TORORO"
  },
  {
    "value": "80",
    "text": "WAKISO"
  },
  {
    "value": "81",
    "text": "YUMBE"
  },
{
    "value": "115",
    "text": "ZOMBO"
  }
]

def get_counties_data(district):
    district_value = district['value']
    url = f'{uri}/ajax/load-counties?district={district_value}'
    response = requests.get(url, timeout=10)
    html_content= f"""{response.text}"""
    # Parse HTML and extract values
    # Regular expression to match option tags and extract value and text
    matches = re.findall(r'<option value="(.*?)">(.*?)</option>', html_content)

    # Convert to desired JSON format and skip the first element
    
    options = [{"value": value, "text": text.strip()} for value, text in matches][1:]
    for option in options:
        get_sub_counties(option['value'])
        #counties_list.extend({option['text']: option['value']})
        #TODO: Save to database
        County.objects.get_or_create(name=option['text'], code=option['value'], district=district_value)
    
  



def get_sub_counties(county):
    
    url = f'{uri}/ajax/load-subcounties?county={county}'
    response = requests.get(url, timeout=10)
    html_content= f"""{response.text}"""
    print(response.status_code)
    # Regular expression to match option tags and extract value and text
    matches = re.findall(r'<option value="(.*?)">(.*?)</option>', html_content)

    # Convert to desired JSON format and skip the first element
    
    options = [{"value": value, "text": text.strip()} for value, text in matches][1:]
    for option in options:
        print(option['text'], option['value'], "sub_counties")
        get_parishes(option['value'])
        #TODO: Save to database
        SubCounty.objects.get_or_create(name=option['text'], code=option['value'], county=county)



def get_parishes(sub_county):
    url = f'{uri}/ajax/load-parishes?subcounty={sub_county}'
    response = requests.get(url, timeout=10)
    html_content= f"""{response.text}"""
    # Regular expression to match option tags and extract value and text
    matches = re.findall(r'<option value="(.*?)">(.*?)</option>', html_content)

    # Convert to desired JSON format and skip the first element
    
    options = [{"value": value, "text": text.strip()} for value, text in matches][1:]
    for option in options:
        print(option['text'], option['value'], "parishes")
        get_villages(option['value'])
        Parish.objects.get_or_create(name=option['text'], code=option['value'], sub_county=sub_county)
       

def get_villages(parish):
    url = f'{uri}/ajax/load-villages?parish={parish}'
    response = requests.get(url, timeout=10)
    html_content= f"""{response.text}"""
    # Regular expression to match option tags and extract value and text
    matches = re.findall(r'<option value="(.*?)">(.*?)</option>', html_content)

    # Convert to desired JSON format and skip the first element
    
    options = [{"value": value, "text": text.strip()} for value, text in matches][1:]
    for option in options:
        print(option['text'], option['value'], "villages") 
        Village.objects.get_or_create(name=option['text'], code=option['value'], parish=parish)

for district in districts:
    # post to the database
    District.objects.get_or_create(name=district['text'], code=district['value'])
    get_counties_data(district)
    

  
#print(counties_list, "counties_list")


