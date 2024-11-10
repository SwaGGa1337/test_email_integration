class EmailSync {
    constructor() {
        this.socket = new WebSocket(
            'ws://' + window.location.host + '/ws/emails/'
        );
        this.progressBar = document.getElementById('progress-bar');
        this.progressText = document.getElementById('progress-text');
        this.emailsTable = document.getElementById('emails-table');
        
        this.initializeWebSocket();
    }

    initializeWebSocket() {
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.socket.onclose = () => {
            console.log('WebSocket connection closed');
        };
    }

    handleMessage(data) {
        switch(data.type) {
            case 'sync_status':
                this.updateProgress(data);
                if (data.status === 'processing') {
                    this.addEmailToTable(data.message);
                }
                break;
            case 'error':
                this.showError(data.message);
                break;
        }
    }

    updateProgress(data) {
        if (data.status === 'processing') {
            const percent = (data.progress / data.total) * 100;
            this.progressBar.style.width = `${percent}%`;
            this.progressText.textContent = 
                `Обработано ${data.progress} из ${data.total} сообщений`;
        } else if (data.status === 'completed') {
            this.progressBar.style.width = '100%';
            this.progressText.textContent = 'Синхронизация завершена';
        }
    }

    addEmailToTable(message) {
        const tbody = this.emailsTable.querySelector('tbody');
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${message.subject}</td>
            <td>${message.sender}</td>
            <td>${message.date}</td>
            <td>${message.attachments ? 
                `<i class="fas fa-paperclip"></i> ${message.attachments}` : 
                ''}</td>
        `;
        tbody.insertBefore(row, tbody.firstChild);
    }

    showError(message) {
        alert(`Ошибка: ${message}`);
    }

    startSync(accountId) {
        this.socket.send(JSON.stringify({
            account_id: accountId
        }));
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    const emailSync = new EmailSync();
    // Получаем ID аккаунта из data-атрибута или другим способом
    const accountId = document.body.dataset.accountId;
    if (accountId) {
        emailSync.startSync(accountId);
    }
}); 