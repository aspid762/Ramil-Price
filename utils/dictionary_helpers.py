from models import Dictionary

def get_dictionary_values(type_name, default_values=None):
    """
    Получает значения из справочника.
    
    Args:
        type_name (str): Тип справочника
        default_values (list): Значения по умолчанию, если справочник пуст
        
    Returns:
        list: Список значений из справочника или значения по умолчанию
    """
    try:
        values = Dictionary.query.filter_by(type=type_name, is_active=True).order_by(Dictionary.sort_order, Dictionary.name).all()
        if values:
            return [value.name for value in values]
    except Exception as e:
        print(f"Ошибка при получении значений из справочника {type_name}: {str(e)}")
    
    return default_values or [] 