import time
import numpy as np
import re
import os
import gc

from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from utils.date_utils import get_date
from utils.csv_utils import load_date, load_url, save_to_csv, save_urls
from utils.csv_utils import save_to_failed_links_csv
from utils.date_utils import is_newer_date

# ubicacion del ejecutable para chromedriver
path = os.getcwd() + '/chromedriver'
#print(path)
#path = '/snap/bin/chromium.chromedriver'
service = Service(executable_path=path)

def get_page_safe_dynamic(url):
    """
    Método para extraer el html de las páginas con los resultados, 
    chequea si hay un error de conexión.

    Parameters
    ----------    
    url : str
        dirección de la oferta

    Returns
    -------
    BeautifulSoup object.
    """  
    chrome_options = Options()
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(service=service, options=chrome_options)        
    try:
        driver.get(url)
        WebDriverWait(driver, 3)
        html = driver.page_source
    except ConnectionError:
        time.sleep(3)
        driver.get(url)
        WebDriverWait(driver, 3)
        html = driver.page_source
    finally:   
        driver.close()
    return BeautifulSoup(html,'html.parser')    

def get_page_dynamic(url):
    """
    Método para extraer el html de las páginas con los resultados.

    Parameters
    ----------
    driver : selenium.webdriver
        instancia del navegador

    url : str
        dirección de la oferta

    Returns
    -------
    BeautifulSoup object.
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=chrome_options)        
        driver.get(url)
        WebDriverWait(driver, 5)\
            .until(EC.presence_of_element_located((By.ID, 'dfpgrid29')))
        html = driver.page_source
    #except Exception as e: 
        #print(e)
    finally:
       driver.close()
    return BeautifulSoup(html,'html.parser')

def results(search_keyword):
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
    bs = get_page_safe_dynamic('https://cl.computrabajo.com/trabajo-de-'\
             +str(search_keyword))

    assert bs.find_all('p', {'class', 'fs24 tc pAll30 mAuto w60 w100_m'}) ==\
        [], 'No se ha encontrado ofertas de trabajo con los filtros actuales'

    num_results = re.sub('[\D]', '', \
                     bs.find('h1', {'class', 'title_page'})\
                     .find('span').text\
                     .split('\r')[0].strip('\n').strip() )
    num_results = int(num_results)    

    assert num_results != 0, 'No se encontraron resultados'
    
    # extraígo los links a las publicaciones
    results = ['#'+re.sub('[a-z,-/]','',tag.a['href'])\
               .split('#')[0] for tag in bs.find_all('article')]
    
    results_dates = [tag.div.find_all('p')[-1].text for tag in bs.find_all('article')]
    
    # resto de páginas
    p = 1
    # chequea si hay botones para la siguiente pagina 
    Contador_ciclo = 0
    boton_sgt_pgn = bs.find_all('span',{'class','b_primary w48 buildLink cp'})
    while boton_sgt_pgn: 
        p += 1
        """
        recorré todas las páginas de resultados desde la 2da si es que hay más paginas que recorrer      
        """
        assert Contador_ciclo < 200, '200 iteraciones en el ciclo'
        try:
            bs = get_page_safe_dynamic('https://cl.computrabajo.com/trabajo-de-'\
                 +str(search_keyword)+'?p='+str(p))
        except:
            continue   
        Contador_ciclo += 1
        assert len(bs.find_all('article')) != 0    
        results += ['?p='+str(p)+'#'+re.sub('[a-z,-/]','',tag.a['href']).split('#')[0] for tag in bs.find_all('article')]
        results_dates += [tag.div.find_all('p')[-1].text for tag in bs.find_all('article')]
        
        boton_sgt_pgn = bs.find_all('span',{'class','b_primary w48 buildLink cp'})  
    # fecha de la última vez que se ejecuto el main_scraper con este item
    try: 
       resume_date = load_date('computrabajo', search_keyword)
    except:
       resume_date = get_date('hace 999 dias')

    # registro donde hubo errores
    retry_links = []   
    retry_links_dates = []  
    
    n = 0
    # raspado
    for index, result_url in enumerate( results):
        time.sleep(np.random.uniform(-0.05,0.05)**2)
        
        date = get_date(results_dates[index])
        try:
            url ='https://cl.computrabajo.com/trabajo-de-'\
                 +str(search_keyword)+result_url 
                    
            # reviso si es una nueva oferta para seguir o no
            if not is_newer_date(date, resume_date) \
                or str(url) in load_url('computrabajo', resume_date, search_keyword):
                continue
            
            # raspo la página
            scrape(url, search_keyword)  
            
            # recoleccion
            if str(date) == str(get_date('hoy')):
                data_row = ['computrabajo',\
                            date,\
                            search_keyword,\
                            url,
                            ]
                save_urls(data_row) 
            
            n+=1
   
        except:
            retry_links.append('https://cl.computrabajo.com/trabajo-de-'\
                 +str(search_keyword)+'#'+result_url )
            retry_links_dates.append(date)
            continue
   
    # intento de nuevo con los que no funcionaron
    failed_links = []
    for index, link in enumerate(retry_links):
        time.sleep(np.random.uniform(-0.05,0.05)**2)
        date = retry_links_dates[index]
        try:
            url = link
            # reviso si es una nueva oferta para seguir o no
            if not is_newer_date(date, resume_date) \
                or str(url) in load_url('computrabajo', resume_date, search_keyword):
                continue
            
            scrape(url, search_keyword)  
            
            # recoleccion
            if str(date) == str(get_date('hoy')):
                data_row = ['computrabajo',\
                            date,\
                            search_keyword,\
                            url,
                            ]
                save_urls(data_row) 
                
            failed_links.append(link)
            #failed_links_dates.remove(date)
            n += 1
        except:
            continue
    
    # guardo los links fallidos en otro csv
    for link in failed_links:
        csv_row=['computrabajo', search_keyword, link]
        save_to_failed_links_csv(csv_row) 

    informe_row = 'computrabajo: ' + str(n)+'/'+str(num_results) 
    try:
        return informe_row
    finally:
        gc.collect()

def scrape(url,search_keyword):
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

    bs = get_page_dynamic(url)
    
    # título
    title = bs.find('p',{'class','title_offer fs21 fwB lh1_2'}).text

    # cuerpo
    body = body_cleanser(bs.find('div',{'class','box_detail'}).find_all('div',{'class', 'fs16'})[1])


    # fecha
    date = get_date(bs.find('p', {'class' ,'fc_aux fs13'}).text)

    # categoría
    category = ''

    # modalidad
    modalidad = ''
    
    # inclusividad
    inclusividad = ''
    
    # ubicación
    try:
        location = ''.join(bs.find('div',{'class','box_detail'})\
                      .find_all('div',{'class', 'fs16'})[0].text.split('\n')[2:])
    except:
        location = ''

    # jornada
    jornada = ''
    try:
        if re.sub('[^\$]','',bs.find_all('span',{'class','tag base mb10'})[-1].text)\
            == '' :       
            jornada = bs.find_all('span',{'class','tag base mb10'})[-1].text
        else: 
            jornada = bs.find_all('span',{'class','tag base mb10'})[-2].text
    except:
        pass
    
    # salario
    salario = ''
    try:
        if re.sub('[^\$]','',bs.find_all('span',{'class','tag base mb10'})[-1].text)\
            != '' :
            salario = bs.find_all('span',{'class','tag base mb10'})[-1].text
        else:
            salario = ''
    except:
        pass
    # publicador
    try:
        publicador = ''.join(bs.find('div',{'class','box_detail'})\
                      .find_all('div',{'class', 'fs16'})[0].text.split('\n')[:2])
    except:
        publicador = ''

    # extras
    try:
        etiquetas = [ tag.text+'; ' for tag in  bs.find_all('span',{'class','tag base mb10'})]
    except:
        etiquetas = []
    etiquetas = ''.join(etiquetas)
     
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
                'computrabajo',
                ]   

    save_to_csv(csv_row)
    # despues de guardar la info se libera ram
    gc.collect()

def body_cleanser(obj):
    """
    Método para limpiar un poco los elementos html del cuerpo de una oferta

    Parameters
    ----------
    obj : tag
        objeto que contiene una o más partes que forman el cuerpo de la 
        oferta.

    Returns
    -------
    body : str
        cuerpo de la oferta ligeramente preprocesado.
    """
    body = ''
    v = obj.text.split('\r')
    for content in v :
        body += content
    return body 
        