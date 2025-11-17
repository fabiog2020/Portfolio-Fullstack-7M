# forms/custom_fields.py
from wtforms import FloatField


class BrazilianFloatField(FloatField):
    """
    Campo numérico que aceita ponto OU vírgula como separador decimal.
    Exemplos válidos: "10.5", "10,5"
    """
    def process_formdata(self, valuelist):
        if valuelist:
            raw = valuelist[0].strip()
            if raw:
                # Troca vírgula por ponto, mas não mexe em mais nada
                normalized = raw.replace(",", ".")
                try:
                    self.data = float(normalized)
                except ValueError:
                    self.data = None
                    raise ValueError(
                        self.gettext(
                            "Informe um número válido. Use ponto ou vírgula como separador decimal."
                        )
                    )
            else:
                self.data = None
        else:
            self.data = None
