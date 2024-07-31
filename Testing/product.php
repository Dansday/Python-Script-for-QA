<?php

class Product
{
    private $prdId;
    private $prodName;
    private $price;
    private $desc;
    private $category;
    private $inventory;
    private $repo;

    public function __construct($repo)
    {
        $this->repo = $repo;
        $this->initializeProduct();
    }

    private function initializeProduct()
    {
        $data = $this->repo->getProductData();
        $this->prdId = $data['id'];
        $this->prodName = $data['name'];
        $this->price = $data['price'];
        $this->desc = $data['description'];
        $this->category = $data['category'];
        $this->inventory = $data['inventory_count'];
    }

    public function getFormattedProductData()
    {
        return [
            'id' => $this->prdId,
            'name' => strtoupper($this->prodName),
            'price' => number_format($this->price, 2),
            'description' => nl2br($this->desc),
            'category' => ucwords($this->category),
            'inventory_count' => $this->inventory
        ];
    }

    public function saveProduct()
    {
        $db = $this->getDatabaseConnection();
        $stmt = $db->prepare("UPDATE products SET name = :name, price = :price, description = :description, category = :category, inventory_count = :inventory_count WHERE id = :id");
        if (!$stmt->execute([
            ':name' => $this->prodName,
            ':price' => $this->price,
            ':description' => $this->desc,
            ':category' => $this->category,
            ':inventory_count' => $this->inventory,
            ':id' => $this->prdId
        ])) {
            throw new Exception('Failed to update product');
        }
    }

    public function decreaseInv($amt)
    {
        if (!is_numeric($amt) || $amt < 0) {
            throw new InvalidArgumentException('Amount must be a positive integer');
        }
        $this->inventory -= $amt;
        $this->saveProduct();
    }

    public function increaseInv($amt)
    {
        if (!is_numeric($amt) || $amt < 0) {
            throw new InvalidArgumentException('Amount must be a positive integer');
        }
        $this->inventory += $amt;
        $this->saveProduct();
    }

    public function sendLowInvAlert()
    {
        if ($this->inventory < 10) {
            // Simulate sending an email alert
            echo "Alert: Low inventory for product ID {$this->prdId}\n";
        }
    }

    public function applyDisc($perc)
    {
        if ($perc < 0 || $perc > 100) {
            throw new Exception('Invalid discount percentage');
        }
        $this->price = $this->price * (1 - $perc / 100);
        $this->saveProduct();
    }

    public function getCatProds()
    {
        $db = $this->getDatabaseConnection();
        $stmt = $db->prepare("SELECT * FROM products WHERE category = :category AND id != :id");
        $stmt->execute([':category' => $this->category, ':id' => $this->prdId]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    private function getDatabaseConnection()
    {
        return new PDO(getenv('DB_DSN'), getenv('DB_USER'), getenv('DB_PASSWORD'));
    }
}
