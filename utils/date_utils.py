import re
import datetime


from datetime import timedelta

def get_date(page_date):    
    """
    Método para encontrár la página con los resultados.

    se aproxima mes a 30 días.


    Parameters
    ----------
    page_date : str
        hace cuanto tiempo se público la oferta

    Returns
    -------
    La fecha en un formato estandarizado.
    """
    current_date = datetime.datetime.now()
    try:
        date_num = float(re.sub( '\D' ,'', page_date).strip())
    except ValueError:
        date_num = 1
    
    time_difference = timedelta(hours = date_num)  
    if ('horas'or'hora') in page_date.split():
        time_difference = timedelta(hours = date_num) 
        date = current_date - time_difference
    
    elif ('hoy' or 'Hoy') in page_date.split():
        date = current_date
        
    elif ('ayer'or 'Ayer') in page_date.split():
        date = current_date - timedelta(days=1)
        
    elif ('mes'or'meses') in page_date.split():
        days = 30*date_num
        date = current_date - timedelta(days = days)
    elif ('Minutos' or 'minutos') in page_date.split():
        date = current_date
    else:
        date = current_date - timedelta(days = date_num)  

    return str(date.day)+'/'+str(date.month)+'/'+str(date.year)   

def is_newer_date(site_date, last_date):
    """
    Método para verificar si site_date es más reciente que
    last_date.

    Parameters
    ----------
    site_date : str
        fecha de publicacion de la oferta.

    last_date : str
        fecha de la última ejecución del WebScraper.

    Returns
    -------
    Boolean.
    """
    sd = site_date.split('/')
    site_date = datetime.datetime(day=int(sd[0]), month=int(sd[1]), year=int(sd[2]))

    ld = last_date.split('/')
    last_date = datetime.datetime(day=int(ld[0]), month=int(ld[1]), year=int(ld[2]))
    return site_date >= last_date