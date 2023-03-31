import time
import re

from scrapers import chiletrabajos
from scrapers import opcionempleo
from scrapers import computrabajo
from scrapers import elmercurio
from scrapers import laborum
from scrapers import indeed
from scrapers import trabajando

# la pagina bloquea la ip por aproximadamente 1 hora
from scrapers import bne
# aparentemente necesita xml.parser 
from scrapers import empleospublicos

from utils.csv_utils import create_dates_csv, new_csv, save_date
from utils.csv_utils import create_failed_links_csv
from utils.csv_utils import create_urls_csv
from utils.date_utils import get_date
from utils.check_utils import csv_check

class Crawler():
    def search(search_keywords, sites):
        """
        Funcion para buscar las search_keywords en los 
        sites especificados

        Parameters
        ----------
        search_keywords : list
            lista con los items de busquedas, deben ser strings.
            
        sites : list
            lista con los nombres de los sitios que realizaran la busqueda.

        Returns
        -------
        None.
        """
        date = get_date('hoy')
        date = re.sub('/', '.', date)
        f = open('informe'+date+'.txt', 'w') 
        f.write( 'datos nuevos en el csv / resultados según la página'+ '\n' )
        f.close()
        
        sites_dict={'chiletrabajos':chiletrabajos ,\
                    'opcionempleo':opcionempleo,\
                    'computrabajo':computrabajo,\
                    'elmercurio':elmercurio,\
                    'laborum':laborum,\
                    'indeed':indeed,\
                    'trabajando':trabajando,\
                    'bne':bne,\
                    'empleospublicos':empleospublicos,
                      }
        
        for search_keyword in search_keywords:
           informe_row = search_keyword + ':' + '\n'
           for site in sites:
                try:
                    informe_row += '    '+sites_dict[site].results(search_keyword)+'\n'
                    save_date([site, get_date('hoy'), search_keyword])
                except AssertionError as e:
                    informe_row += '    '+site +': '+ str(e) +'\n'
                except Exception as e:
                    informe_row += '    '+site +': '+ str(e) +'\n'
                time.sleep(5)
                    
           with open('informe'+date+'.txt', 'a') as f:
                f.write( informe_row )
                f.write('-------------------------------------------------'+'\n')
           
    def reset_data_base(csv_name):
        """ Limpia documentos y csv existentes para empezar de nuevo """
        # intancio nuevos csv
        new_csv(csv_name)
        create_failed_links_csv()
        create_urls_csv()
        create_dates_csv()

    def check(sites):
        csv_check(sites)
    
