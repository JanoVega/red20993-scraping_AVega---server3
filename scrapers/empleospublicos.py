import time
import numpy as np
import re
import os
import gc

from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys


from utils.date_utils import get_date
from utils.csv_utils import save_to_csv
from utils.csv_utils import save_to_failed_links_csv
from utils.date_utils import is_newer_date

# ubicacion del ejecutable para chromedriver
path = os.getcwd() + '/chromedriver'
service = Service(executable_path=path)

"""
No Funciona
Aparentemente necesita usar xml.parser para BeautifulSoup
"""


def results(search_keyword, url_collector):
    """
    Método que recorre las páginas con los resultados

    Parameters
    ----------
    search_keyword : str
        Item para buscar en la página.

    Returns
    -------
    None
    """  
    url_collector.reset()
    
    url ='https://www.empleospublicos.cl/' 
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(url)
        
        # escribo la consulta en la barra de busqueda
        text_input = driver.find_element(By.NAME, "q")
        ActionChains(driver)\
            .send_keys_to_element(text_input, search_keyword )\
            .perform()
        
        time.sleep(10)
        html = driver.page_source
        bs = BeautifulSoup(html,'html.parser')
        assert not bs.find_all('ul',{'class', 'typeahead__list empty'}),\
                                        'no se encontraron resultados'
            
        num_results = len(bs.find_all('li',{'class', 'typeahead__item'}))
        
        # donde hubo errores en scrape
        failed_links = [] 
        n=0
        for i in range(num_results):
            
            
            # selecciono la oferta i
            for _ in range(i+1):
                ActionChains(driver)\
                .send_keys(Keys.ARROW_DOWN)\
                .perform()
            print(1)
            # abro la oferta
            ActionChains(driver)\
            .send_keys(Keys.ENTER)\
            .perform()          
            
            # cambio de pestaña
            driver.switch_to.window(driver.window_handles[-1])
                    # WebDriverWait(driver, 4).\
                    #    until(EC.presence_of_element_located((By.ID, 'lblAvisoTrabajo')))
            print(2)
            # raspado
            html = driver.page_source
            bs = BeautifulSoup(html,'html.parser')
            url = driver.current_url
            try:
                print(-1)
                scrape(bs, url,search_keyword, url_collector)
                n+=1
            except:
                print(-2)
                failed_links.append(driver.current_url)
                continue
            finally:
                print(3)
                # cierro y cambio ventana
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                
                print(4)
                # elimino lo que estaba en la barra de busqueda
                botonn_locator = locate_with(By.TAG_NAME, "span")\
                                    .to_right_of({By.NAME: "q"})                    
                boton   = driver.find_element(botonn_locator) 
                ActionChains(driver)\
                    .click(boton)\
                    .perform()
                print(5)
                # escribo de nuevo la consulta
                text_input = driver.find_element(By.NAME, "q")
                ActionChains(driver)\
                .send_keys_to_element(text_input, search_keyword )\
                .perform()

    finally:
        driver.quit()
        
        url_collector.end_collect('bne', search_keyword) 
        
        informe_row = 'empleospublicos: ' + str(n)+'/'+str(num_results) 
        try:
            return informe_row
        finally:
            gc.collect


def scrape(bs, url ,search_keyword, url_collector):
    """
    Método que extrae y guarda la información de la página de una
     oferta

    Parameters
    ----------
    url : str
        dirección web de la oferta.
    search_keyword : str
        Item buscado.

    Returns
    -------
    None

    """ 
    # fecha de la última vez que se ejecuto el main_scraper con este item
    try: 
       resume_date = np.load(os.getcwd() \
        +'/crawler_search_dates/'+search_keyword+'_resume_date.npy')[0]
    except:
        resume_date = get_date('hace 999 dias')
    
    # título
    title = bs.find('h2').text

    spans = [span for span in bs.find_all('div',{'class','col-md-12'})[1]\
                                    .find_all('span')[11:-4]]
    # cuerpo
    body = [ span.text for span in spans[1:7]]
    body = ''.join(body)


    # fecha
    date = ''

    # categoría
    category = bs.find_all('span')[7].find_all('p')[3].text

    # modalidad
    modalidad = ''
    
    # inclusividad
    inclusividad = ''
    
    # ubicación
    try:
        location = bs.find_all('span')[7].find_all('p')[4].text \
                    +', '+bs.find_all('span')[7].find_all('p')[5].text
    except:
        location = ''

    # jornada
    try:
        jornada = spans[0].find_all('strong')[4]\
                .parent.nextSibling.nextSibling.text
    except:
        jornada = ''
    
    # salario
    try:
        salario = bs.find_all('ul',{'class', 'e05_form1Columna'})[1]\
                    .find('h3').nextSibling.nextSibling
    except:
        salario = ''
    # publicador
    publicador = bs.find_all('span')[7].find_all('p')[0].text

    # extras
    etiquetas = ''

    csv_row = [ str(search_keyword),\
                category.strip('\n'),\
                title.strip('\n'),\
                body.strip('\n'),\
                date,\
                location,\
                modalidad,\
                jornada,\
                inclusividad,\
                salario,\
                publicador,\
                etiquetas,\
                url,\
                'empleospublicos',
                ]   

    # recoleccion
    if str(date) == str(get_date('hoy')):
        url_collector.collect_url(url)    
    # reviso si es una nueva oferta para seguir o no
    if not is_newer_date(date, resume_date) \
        or str(url) in url_collector.load_data('empleospublicos', search_keyword):
        return

    save_to_csv(csv_row)
    # despues de guardar la info se libera ram
    gc.collect
