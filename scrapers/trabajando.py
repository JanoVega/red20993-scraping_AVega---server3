import re
import os
import gc

from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.chrome.service import Service

from utils.date_utils import get_date
from utils.date_utils import is_newer_date
from utils.csv_utils import load_date, load_url, save_to_csv, save_urls
from utils.csv_utils import save_to_failed_links_csv

# ubicacion del ejecutable para chromedriver 
path = os.getcwd() + '/chromedriver'
#path = '/snap/bin/chromium.chromedriver'
service = Service(executable_path=path)

def get_to_page(driver, url, search_keyword):
    """
    Método para encontrár la página con los resultados.

    Parameters
    ----------
    driver : selenium.webdriver
        instancia del navegador

    url : str
        dirección de la pagina en donde se realizará la busqueda

    search_keyword : str
        ítem de busqueda

    Returns
    -------
    None
    """
    
    driver.get(url)

    # Espero que aparesca la barra de busqueda
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'search')))
    
    # Encuentra la barra de busqueda
    search_bar = driver.find_element(By.ID, "search")
    text_input =  search_bar.find_elements(By.TAG_NAME, 'div')[0]
    
    # Se mueve el cursor a la barra de busqueda
    ActionChains(driver)\
        .move_to_element(text_input)\
        .perform()

    # ingreso la consulta (search_keyword)
    ActionChains(driver)\
        .send_keys_to_element(text_input, search_keyword )\
        .perform()
    
    # úbico el boton de busqueda
    botonn_locator = locate_with(By.TAG_NAME, "button")\
                    .to_right_of({By.TAG_NAME: "span"})
    boton   = driver.find_element(botonn_locator) 
    
    # presiono el botón
    ActionChains(driver)\
        .click(boton)\
        .perform()
        
def Click_more_results(driver):
    """
    #Método para simular el scroll down del mause.
    Hago click en más resultados


    Parameters
    ----------
    driver : selenium.webdriver
        instancia del navegador

    Returns
    -------
    None
    """
    #ofert_locator = locate_with(By.TAG_NAME, "div")\
    #                .below({By.ID: "overlayListado"})
    #footer = driver.find_element(ofert_locator)
    
    # scroll down
    #scroll_origin = ScrollOrigin.from_element(footer, 0, +50)
    #ActionChains(driver)\
    #    .scroll_from_origin(scroll_origin, 0, 2000)\
    #    .perform()
    try:  
        boton   = driver.find_element(By.LINK_TEXT, "Acepto")
        ActionChains(driver)\
            .click(boton)\
            .perform()
    except:
        pass
    
    
    offert_list =  driver.find_element(By.ID, "listadoOfertas")
    boton   = offert_list.find_element(By.TAG_NAME, "button")
                        
    ActionChains(driver)\
        .click(boton)\
        .perform()
    
    # Añadieron un boton para mostrar más resultados
    
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
    # abro chrome para extraer los datos de la oferta
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # espera hasta 1 seg a que aparesca un item de la página antes de extraer el html
        driver.get(url)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'offerHeader')))
        html = driver.page_source
    finally:
        driver.close()
    return BeautifulSoup(html, 'html.parser')

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
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    url = 'https://www.trabajando.cl/'
    get_to_page(driver, url, search_keyword)
    
    WebDriverWait(driver, 8)\
        .until(EC.presence_of_element_located((By.ID, 'detalleOferta')))

    # extraígo el html
    html = driver.page_source
    bs = BeautifulSoup(html,'html.parser')

    # trato de extraer el número de resultados, 
    # si no funciona, "recargo la página"
    assert not bs.find_all('h2',{'class','h3 mx-auto'}),\
        'No hay ofertas de trabajo para tu búsqueda'

    try:
        num_results = re.sub('[\D]', '',bs.find('span',{'class', \
                    'searched-results'})\
                        .text.split()[0] )
        num_results = int(num_results )
    except:
        html = driver.page_source
        bs = BeautifulSoup(html,'html.parser')
        num_results = re.sub('[\D]', '',bs.find('span',{'class', \
                    'searched-results'})\
                        .text.split()[0] )
        num_results = int(num_results ) 

    n = 0
    # fecha de la última vez que se ejecuto el main_scraper con este item
    try: 
        resume_date = load_date('trabajando', search_keyword)
    except:
        resume_date = get_date('hace 999 dias')
        
    results = []
    results_dates = []
    # hago un "scroll down" hasta obtener todas las otras ofertas, 
    # voy guardando los links de estas.
    p=1
    Contador_ciclo = 0
    while len(results)/(num_results-1)<0.9:
    
        html = driver.page_source
        bs = BeautifulSoup(html,'html.parser')
        assert Contador_ciclo < 200, '200 iteraciones en el ciclo'
        if len(bs.find_all('div', {'class', 'result-box d-flex position-relative overflow-hidden'})) !=0 :
                results += [tag.a['href'] for tag in bs.find_all('div',\
                                    {'class', 'result-box d-flex position-relative overflow-hidden'})]
                results_dates += [get_date(tag.find_all('div')[-1].span.text) \
                                    for tag in bs.find_all('div',\
                                    {'class', 'result-box d-flex position-relative overflow-hidden'})]
                p += 1
        try:
            WebDriverWait(driver, 1)
            Click_more_results(driver)
        except Exception as e:
            #print(e) , el error ocurre cuando no hayan mas cosos que sacar
            break
        Contador_ciclo += 1
        #print(len(results), '/', num_results)
    try:
       0
    finally:
        driver.quit()

    retry_links = []
    retry_links_dates = []
    # itero sobre los links de ofertas extraídos 
    for index, result_url in enumerate(results):
        date = results_dates[index]
        try:
            url = 'https://www.trabajando.cl'+ result_url
            # reviso si es una nueva oferta para seguir o no
            if not is_newer_date(date, resume_date) \
                or str(url) in load_url('trabajando', resume_date, search_keyword):
                continue
            #raspado
            scrape(url, search_keyword)
            
            # recoleccion
            if str(date) == str(get_date('hoy')):
                data_row = ['trabajando',\
                            date,\
                            search_keyword,\
                            url,
                            ]
                save_urls(data_row) 
                
            n += 1
        except Exception as e:
            #print(e)
            retry_links.append(result_url)
            retry_links_dates.append(date)
            
    failed_links = []
    # intento de nuevo con los que no funcionaron
    for index, link in enumerate(retry_links):
        date = retry_links_dates[index]
        try:
            url = link
            # reviso si es una nueva oferta para seguir o no
            if not is_newer_date(date, resume_date) \
                or str(url) in load_url('trabajando', resume_date, search_keyword):
                continue
            scrape(url, search_keyword, first = False )
            # recoleccion
            if str(date) == str(get_date('hoy')):
                data_row = ['trabajando',\
                            date,\
                            search_keyword,\
                            url,
                            ]
                save_urls(data_row) 
            failed_links.append(link)
            n += 1
        except:
            pass

    # guardo los links fallidos en otro csv
    for link in failed_links:
        csv_row=['trabajando', search_keyword, link]
        save_to_failed_links_csv(csv_row) 

    informe_row = 'trabajando: ' + str(n)+'/'+str(num_results) 
    try:
        return informe_row
    finally:
        gc.collect() 

def scrape(url, search_keyword):
    """
    Método que extrae y guarda la información de la página de una
     oferta

    Parameters
    ----------
    driver : selenium.webdriver
        instancia del navegador

    url : str
        dirección web de la oferta.

    search_keyword : str
        Item buscado.


    Returns
    -------
    None

    """
    bs = get_page_dynamic(url)
    # fecha
    date = get_date(bs.find('span', {'class', 'd-block'}).text)

    # para la primera oferta, cambian un par de detalles

    title = bs.find('div',{'title offerHeader'}).find('h2').text
    body =  body_cleanser(bs.find('div',{'description text-break'}))

    try:
        publicador = bs.find('div',{'title offerHeader'}).find('a').text
    except:
        publicador = ''

    spans = bs.find('ul',{'badges d-flex align-items-center flex-wrap'}).find_all('li')

    for i,span in enumerate(spans):
        if span.text.strip().split()[0] == 'Región':
            index=i
   
    # ubicación
    try:
        location= spans[index].text + ',' +spans[index+1].text
    except:
        location=''

    # modalidad
    modalidades=['Presencial','Mixta (Teletrabajo + Presencial)','Teletrabajo']
    modalidad = ''
    try:
        for span in spans:
            if span.text.strip() in modalidades:
                modalidad= span.text.strip()
                break
    except:
        modalidad= ''
    
    # categoria
    category = ''
    
    # jornada
    jornada = ''
    
    # inclusividad
    inclusividad = 'si' if bs.find_all('i', {'class', \
        'fa-solid fa-wheelchair-move'}) else 'no'
    # salario
    try:
        salario = bs.find('h4',{'class','mb-0'}).text.strip()
    except:
        salario = ''
    # publicador
    # extras
    try:
        etiquetas = [tag.text + '; ' for tag in spans]
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
                'trabajando',
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
