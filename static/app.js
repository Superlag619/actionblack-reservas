document.getElementById('configForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const hora = document.getElementById('hora_clase').value;
    const tipo = document.getElementById('tipo_clase').value;
    const sede = document.getElementById('sede').value;
    
    const status = document.getElementById('status');
    status.textContent = 'Guardando...';
    status.className = '';
    
    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `hora_clase=${hora}&tipo_clase=${tipo}&sede=${sede}`
        });
        
        const result = await response.json();
        status.textContent = '✅ Configuración guardada correctamente';
        status.className = 'success';
    } catch (error) {
        status.textContent = '❌ Error al guardar';
        status.className = 'error';
    }
});
