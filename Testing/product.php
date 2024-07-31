<?php

class Product
{
    private $prdId;
    private $prodName;
    private $price;
    private $desc;
    private $category;
    private $inventory;

    public function __construct($repo)
    {
        // Fetch data from repository and initialize properties
        $data = $repo->getProductData();
        $this->prdId = $data['id'];
        $this->prodName = $data['name'];
        $this->price = $data['price'];
        $this->desc = $data['description'];
        $this->category = $data['category'];
        $this->inventory = $data['inventory_count'];
    }

    public function getFormattedProductData()
    {
        // Formatting data
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
        $db = new PDO('mysql:host=localhost;dbname=testdb', 'root', '');
        $stmt = $db->prepare("UPDATE products SET name = :name, price = :price, description = :description, category = :category, inventory_count = :inventory_count WHERE id = :id");
        $stmt->execute([
            ':name' => $this->prodName,
            ':price' => $this->price,
            ':description' => $this->desc,
            ':category' => $this->category,
            ':inventory_count' => $this->inventory,
            ':id' => $this->prdId
        ]);
    }

    public function decreaseInv($amt)
    {
        if ($this->inventory >= $amt) {
            $this->inventory -= $amt;
            $this->saveProduct();
        } else {
            throw new Exception('Not enough inventory');
        }
    }

    public function increaseInv($amt)
    {
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
        $this->price = $this->price * (1 - $perc / 100);
        $this->saveProduct();
    }

    public function getCatProds()
    {
        $db = new PDO('mysql:host=localhost;dbname=testdb', 'root', '');
        $stmt = $db->prepare("SELECT * FROM products WHERE category = :category AND id != :id");
        $stmt->execute([':category' => $this->category, ':id' => $this->prdId]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
}
