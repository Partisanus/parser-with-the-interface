import sqlite3
import sys
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QComboBox, QCheckBox

class Main(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()
        self.combox(0)
        self.header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 YaBrowser/21.5.3.742 Yowser/2.5 Safari/537.36"
        }

    def initUI(self):
        self.resize(700, 400) #окно которое возможно менять размер
        self.setWindowTitle('Parser data')
        self.qlab1 = QLabel(self) #это поле вывода информации оно по умолчанию невидимо
        self.qlab1.setGeometry(30, 120, 640, 250)
        qlab_style = 'border: 2px solid black' #все что можно в стилях сделать можно внести
        self.qlab1.setStyleSheet(qlab_style)
        self.combbox1_0 = QComboBox(self)
        self.combbox1_0.setGeometry(30, 30, 130, 25)
        self.combbox1_0.addItems(['mebelshara', 'tui', 'tvoyaapteka'])
        self.combbox1_0.activated.connect(self.combox) #приписываем функцию комбобокусу пока выводит в консоль
        self.btn1 = QPushButton('Start', self)  # btn это имя элемента (виджета)
        self.btn1.setGeometry(190, 30, 100, 25)  # первые 2 цифры это отступы от верха и слева, вторые 2 цифры размер по ширине и высоте
        self.btn1.clicked.connect(self.func1)  # делаем реакцию на клик кнопки
        self.cbjson = QCheckBox('Save JSON', self)
        self.cbjson.move(30, 70)
        self.cbjson.toggle()
        self.cbdb = QCheckBox('Save DB', self)
        self.cbdb.move(140, 70)

    def combox(self,ind): #ind = позиция элемента в комбобоксе
        self.ind1 = ind

    def ch_comb(self):
        if self.ind1 == 0:
            return self.pars_mebelshara()
        elif self.ind1 == 1:
            return self.pars_tui()
        elif self.ind1 == 2:
            return self.pars_tvoyaapteka()

    def func1(self):
        datas = self.ch_comb()
        if self.cbjson.isChecked():
            if self.cbdb.isChecked():
                self.qlab1.setText(f'Data collection from {datas[0]} site has started, it may take a few minutes.')
                self.save_file(datas[0], datas[1])
                self.ins_db(datas[0], datas[1])
            else:
                self.qlab1.setText(f'Data collection from {datas[0]} site has started, it may take a few minutes.')
                self.save_file(datas[0], datas[1])
        else:
            if self.cbdb.isChecked():
                self.qlab1.setText(f'Data collection from {datas[0]} site has started, it may take a few minutes.')
                self.ins_db(datas[0], datas[1])
            else:
                self.qlab1.setText('Choose where to save the data')

    def save_file(self, file, data):
        with open(f"{file}.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=3, ensure_ascii=False)


    def ins_db(self, name, datas):
        conn = sqlite3.connect(f'{name}.db')  # создает или подключается к существующему файлу БД
        cursor = conn.cursor()
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS {name} (id INTEGER PRIMARY KEY AUTOINCREMENT, address TEXT, latlon TEXT, name TEXT, phones TEXT, working_hours TEXT)''')
        for i in datas:
            data = []
            for k in i:
                data.append(str(i[k]))
            cursor.execute(f'''INSERT INTO {name} (address, latlon, name, phones, working_hours) VALUES (?,?,?,?,?)''', data,)  # вставка данных через переменные
            conn.commit()

#------ сайт 1 mebelshara

    def req_get (self, *args):
        if args[0] == 1:
            data = requests.get(args[1], headers=self.header)
        elif args[0] == 2:
            data = requests.get(args[1], headers={'User-Agent': UserAgent().chrome})
        elif args[0] == 3:
            data = requests.get(args[1], headers=self.header, cookies= args[2])
        return BeautifulSoup(data.text, 'html.parser')

    def times(self, work, weekends):
        times = []
        if 'Без выходных' in work:
            time = f"пн-вс {weekends.replace('Время работы: ', '').replace(' - ', '-').replace(': ', ' ')}"
            times.append(time)
        else:
            times.append(work.replace('Время работы: ', '').replace(' - ', '-').replace(': ', ' '))
            times.append(weekends.replace('Время работы: ', '').replace(' - ', '-').replace(': ', ' '))
        return times

    def pars_mebelshara(self):
        soup = self.req_get(2, 'https://www.mebelshara.ru/contacts')
        element = soup.find_all('div', attrs={'class': "city-item"})
        datas = []
        for i in element:
            elem1 = i.find('h4', attrs={'class': "js-city-name"}).get_text()
            elems = i.find_all('div', attrs={'class': "shop-list-item"})
            for k in elems:
                dict1 = {}
                adr = k['data-shop-address']
                dict1['adress'] = f"{elem1}, {k['data-shop-address']}"
                cord = f"{k['data-shop-latitude']} {k['data-shop-longitude']}"
                dict1['latlon'] = [k['data-shop-latitude'], k['data-shop-longitude']]
                name = k['data-shop-name']
                dict1['name'] = k['data-shop-name']
                phon = k['data-shop-phone']
                dict1['phones'] = [k['data-shop-phone']]
                time1 = k.find('div', attrs={'class': "shop-weekends"}).get_text()
                time = self.times(k['data-shop-mode1'], time1)
                dict1['working_hours'] = time
                datas.append(dict1)
        return 'mebelshara', datas

# #--------- сайт 2 tui
# # --------------Получаем организации в городе-----------------
    def offices(self, id):
        soup = self.req_get(1, f'https://apigate.tui.ru/api/office/list?cityId={id}')
        data = json.loads(str(soup))
        offices_city = []
        store = data['offices']
        for i in store:
            office = {}
            tim1 = i['hoursOfOperation']
            time = []
            if not tim1['workdays']['isDayOff']:
                time.append(f"пн-пт {tim1['workdays']['startStr']}-{tim1['workdays']['endStr']}")
            else:
                time['workdays'] = 'пн- пт выходные'
            if not tim1['saturday']['isDayOff'] and not tim1['sunday']['isDayOff']:
                if tim1['saturday']['startStr'] == tim1['sunday']['startStr'] and tim1['saturday']['endStr'] == tim1['sunday']['endStr']:
                    time.append(f"сб-вс {tim1['saturday']['startStr']}-{tim1['saturday']['endStr']}")
                else:
                    time.append(f"сб {tim1['saturday']['startStr']}-{tim1['saturday']['endStr']}")
                    time.append(f"вс {tim1['sunday']['startStr']}-{tim1['sunday']['endStr']}")
            elif tim1['saturday']['isDayOff'] and tim1['sunday']['isDayOff']:
                time.append(f"сб-вс выходной")
            else:
                if not tim1['saturday']['isDayOff']:
                    time.append(f"сб {tim1['saturday']['startStr']}-{tim1['saturday']['endStr']}")
                else:
                    time.append(f"сб выходной")
                if not tim1['sunday']['isDayOff']:
                    time.append(f"вс {tim1['sunday']['startStr']}-{tim1['sunday']['endStr']}")
                else:
                    time.append(f"вс выходной")
            office["address"] = i['address']
            office["latlon"] = [i["latitude"], i["longitude"]]
            office["name"] = i['name']
            office["phones"] = [i['phones'][0]['phone'], i['phones'][0]['url'][4:]]
            office["working_hours"] = time
            offices_city.append(office)
        return offices_city

    def pars_tui(self):
        soup = self.req_get(1, 'https://apigate.tui.ru/api/office/cities')
        data = json.loads(str(soup))
        store = data['cities']
        datas = []
        for i in store:
            datas += self.offices(i['cityId'])
        return 'tui', datas

#-------- сайт 3 tvoyaapteka

    def pars_tvoyaapteka(self):
        soup = self.req_get(1, 'https://www.tvoyaapteka.ru/adresa-aptek/')
        towns = soup.find('div', attrs={'class':"town_list_xs panel_inner"}).find_all('a', attrs={'class':"town"})
        all_citys = {}
        datas = []
        for i in towns:
            all_citys[i.get_text().strip()] = i['data-id']
            datas += self.data_tvoyaapteka(i['data-id'], i.get_text().strip())
        return 'tvoyaapteka', datas

    def replaced(self, i, repl):
        days2 = i
        for k in range(0, len(repl)-1, 2):
            days2 = days2.replace(repl[k], repl[k + 1]).strip()
        if len(days2) > 6:
            if days2[3].isdigit() and not days2[4].isdigit():
                days2 = days2.replace(days2[3], f'0{days2[3]}', 1)

            elif days2[6].isdigit() and not days2[7].isdigit():
                days2 = days2.replace(days2[6], f'0{days2[6]}', 1)
        else:
            days2 = days2.replace(days2[0:len(days2) - 1], days2[0:2] + ' выходной')
        return days2

    def data_tvoyaapteka(self, id_city, city):
        soup = self.req_get(3, 'https://www.tvoyaapteka.ru/adresa-aptek/', {" BITRIX_SM_S_CITY_ID": id_city})
        phone = (soup.find('div', attrs={'class': 'number'}).get_text().strip())
        element = soup.find('div', attrs={'id': "address_aptek_list"}).find_all('div', attrs={'class': "apteka_item"})
        city_data = []
        for i in element:
            datas = {}
            datas['address'] = f"{city}, {i.find('div', attrs={'class': 'apteka_address'}).get_text()}"
            datas['latlon'] = [i['data-lat'], i['data-lon']]
            datas['name'] = i.find('div', attrs={'class': 'apteka_title'}).get_text().strip()
            datas['phones'] = [phone]
            time = " ".join(i.find('div', attrs={'class': 'apteka_time'}).get_text().split()).lower()
            work_times = []
            days1 = time.replace(', ', ';').replace('; ', ';').replace(' сб', ';сб').replace(' вс', ';вс').replace(' (', ';(').split(';')
            if 'ежедневно' in time:
                if len(days1) > 1:
                    wdays = []
                    for i in days1:
                        if 'ежедневно с' in i:
                            repl = ['ежедневно с', 'пн-пт', 'сб - вс', 'сб-вс', ': в', ' в', ' с ', ' ', ': с', '',
                                    ' до ', '-', ': ', ' ', '.', ':']
                            wdays.append(self.replaced(i, repl))
                        else:
                            repl = ['ежедневно', '', 'сб - вс', 'сб-вс', ': в', ' в', ' с ', ' ', ': с', '', ' до ',
                                    '-',  ': ', ' ', '.', ':']
                            wdays.append(self.replaced(i, repl))
                    work_times = wdays
                else:
                    repl = ['ежедневно с', 'пн-вс', 'сб - вс', 'сб-вс', ': в', ' в', ' с ', ' ', ': с', '', ' до ', '-', ': ', ' ', '.', ':']
                    work_times.append(self.replaced(days1[0], repl))
            elif 'круглосуточно' in time:
                work_times.append('пн-вс 00:00-24:00')
            datas['working_hours'] = work_times
            city_data.append(datas)
        return city_data

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    ex.show()
    sys.exit(app.exec_())
