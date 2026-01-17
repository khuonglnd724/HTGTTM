/* API Client Module */

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL || '';
    }

    async request(method, endpoint, data = null) {
        const url = this.baseURL + endpoint;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async get(endpoint) {
        return this.request('GET', endpoint);
    }

    async post(endpoint, data) {
        return this.request('POST', endpoint, data);
    }

    async put(endpoint, data) {
        return this.request('PUT', endpoint, data);
    }

    async delete(endpoint) {
        return this.request('DELETE', endpoint);
    }

    async delete(endpoint) {
        return this.request('DELETE', endpoint);
    }

    async uploadFile(endpoint, file) {
        const formData = new FormData();
        formData.append('file', file);

        const url = this.baseURL + endpoint;
        const options = {
            method: 'POST',
            body: formData
        };

        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Upload Error:', error);
            throw error;
        }
    }
}

// Create global API client
const api = new APIClient('/api');
