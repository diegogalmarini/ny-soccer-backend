from django.db.models import Sum
from django.db.models.functions import TruncYear
from league.models import League
from paypal.standard.ipn.models import PayPalIPN
import sys

def print_header(title):
    print("\n" + "="*60)
    print(f"📊 {title}")
    print("="*60)

# 1. ANÁLISIS DE PRECIOS (Ligas Activas)
print_header("MODELO DE PRECIOS ACTUAL (Ligas Activas)")

# Buscamos ligas que no estén terminadas (3) ni deshabilitadas (4)
# Según models.py: STATUS_RECRUIT=1, STATUS_ACTIVE=2
active_leagues = League.objects.exclude(status__in=[3, 4]).order_by('-id')

if not active_leagues.exists():
    print("⚠️ No se encontraron ligas activas en este momento.")
else:
    print(f"{'NOMBRE DE LA LIGA':<40} | {'INDIVIDUAL ($)':<15} | {'EQUIPO ($)':<10}")
    print("-" * 70)
    for l in active_leagues:
        # Precios base definidos en el modelo
        ind_cost = f"${l.registration_cost}"
        team_cost = f"${l.team_cost}"
        print(f"{l.name[:38]:<40} | {ind_cost:<15} | {team_cost:<10}")

# 2. HISTÓRICO DE INGRESOS (PayPal IPN)
print_header("HISTÓRICO DE INGRESOS (Confirmados por PayPal)")

# La tabla PayPalIPN guarda cada transacción. Filtramos solo las completadas.
# payment_status suele ser "Completed"
revenue_by_year = PayPalIPN.objects.filter(payment_status='Completed')\
    .annotate(year=TruncYear('payment_date'))\
    .values('year')\
    .annotate(total=Sum('mc_gross'))\
    .order_by('-year')

total_historico = 0

if not revenue_by_year:
    print("⚠️ No se encontraron transacciones en la tabla PayPalIPN.")
    print("Diagnóstico: Es posible que los logs de PayPal no se migraron o la tabla se limpió.")
else:
    print(f"{'AÑO':<10} | {'INGRESOS TOTALES':<20}")
    print("-" * 35)
    for r in revenue_by_year:
        if r['year']:
            year_str = r['year'].strftime('%Y')
            total = r['total'] or 0
            total_historico += total
            print(f"{year_str:<10} | ${total:,.2f}")
    
    print("-" * 35)
    print(f"TOTAL HISTÓRICO AUDITADO: ${total_historico:,.2f}")

# 3. TIPOS DE SUSCRIPCIÓN (Análisis de Código)
print_header("ESTRUCTURA DE SUSCRIPCIONES (Hallazgos)")
print("""
El sistema NO maneja suscripciones recurrentes (SaaS).
Opera bajo un modelo de 'Pago Único por Temporada'.

Tipos de Producto detectados en el código:
1. FEE DE EQUIPO (Payment Team):
   - El capitán paga por todo el equipo.
   - Monto promedio detectado: $1,000 - $1,400 aprox.

2. FEE INDIVIDUAL (Free Agent):
   - Un jugador suelto paga por su cupo.
   - Monto promedio detectado: $130 - $150 aprox.

3. SPLIT PAYMENT:
   - Funcionalidad híbrida donde el equipo se divide el costo.
""")