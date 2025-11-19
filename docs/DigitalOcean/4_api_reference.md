# 4. DigitalOcean API Reference

This document provides a reference for the key DigitalOcean API endpoints used in this project. For a complete and detailed API reference, please refer to the [official DigitalOcean API documentation](https://developers.digitalocean.com/documentation/v2/).

## Endpoints

### Droplets

#### `POST /v2/droplets`

*   **Description:** Creates a new Droplet.
*   **Parameters:**
    *   `name` (string, required): The name of the Droplet.
    *   `region` (string, required): The region to create the Droplet in (e.g., `nyc3`).
    *   `size` (string, required): The size slug of the Droplet (e.g., `s-1vcpu-1gb`).
    *   `image` (string, required): The image ID or slug to use for the Droplet (e.g., `ubuntu-20-04-x64`).
    *   `ssh_keys` (array, optional): An array of SSH key IDs or fingerprints to embed in the Droplet's root user's authorized_keys file.
    *   `user_data` (string, optional): A script that will be executed on the Droplet when it is created.
*   **Request Body Example:**
    ```json
    {
      "name": "My-New-Droplet",
      "region": "nyc3",
      "size": "s-1vcpu-1gb",
      "image": "ubuntu-20-04-x64"
    }
    ```
*   **Response Example:**
    ```json
    {
      "droplet": {
        "id": 123456789,
        "name": "My-New-Droplet",
        "memory": 1024,
        "vcpus": 1,
        "disk": 25,
        "region": { ... },
        "image": { ... },
        "size": { ... },
        "networks": { ... },
        "status": "new"
      }
    }
    ```

#### `GET /v2/droplets`

*   **Description:** Lists all Droplets.
*   **Response Example:**
    ```json
    {
      "droplets": [
        {
          "id": 123456789,
          "name": "My-New-Droplet",
          ...
        }
      ]
    }
    ```

#### `GET /v2/droplets/{droplet_id}`

*   **Description:** Retrieves a specific Droplet by its ID.

#### `DELETE /v2/droplets/{droplet_id}`

*   **Description:** Deletes a specific Droplet by its ID.

### Droplet Actions

#### `POST /v2/droplets/{droplet_id}/actions`

*   **Description:** Performs an action on a Droplet (e.g., reboot, power cycle, shutdown).
*   **Request Body Example (Reboot):**
    ```json
    {
      "type": "reboot"
    }
    ```
