#!/bin/bash

echo "🧪 Esecuzione Test Suite Completa"
echo "=================================="
echo ""

# Attiva virtual environment
source venv/bin/activate

echo "🍳 Testing Kitchen Service..."
cd kitchen_service
python -m pytest test/kitchen_test.py test/menu_test.py test/status_test.py -v --tb=short
KITCHEN_RESULT=$?
cd ..

echo ""
echo "🚦 Testing Routing Service..."
cd routing_service
python -m pytest test/ -v --tb=short
ROUTING_RESULT=$?
cd ..

echo ""
echo "🍽️ Testing Menu Service..."
cd menu_service
python -m pytest test/ -v --tb=short
MENU_RESULT=$?
cd ..

echo ""
echo "=================================="
echo "📊 Risultati Finali"
echo "=================================="
echo "Kitchen Service: $([ $KITCHEN_RESULT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo "Routing Service: $([ $ROUTING_RESULT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo "Menu Service:    $([ $MENU_RESULT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo ""

if [ $KITCHEN_RESULT -eq 0 ] && [ $ROUTING_RESULT -eq 0 ] && [ $MENU_RESULT -eq 0 ]; then
    echo "🎉 Tutti i test sono passati!"
    exit 0
else
    echo "⚠️ Alcuni test sono falliti"
    exit 1
fi

