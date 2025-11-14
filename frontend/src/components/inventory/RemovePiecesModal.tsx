import React, { useState, useEffect } from 'react';
import { api } from '../../utils/api';

interface Product {
  id: number;
  name: string;
  codigo?: string;
  stock: number;
}

interface RemovePiecesModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const RemovePiecesModal: React.FC<RemovePiecesModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<number | ''>('');
  const [quantity, setQuantity] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadProducts();
    }
  }, [isOpen]);

  const loadProducts = async () => {
    setLoadingProducts(true);
    try {
      const response = await api.get('/products/', { params: { active: true } });
      setProducts(response.data.filter((p: Product) => p.stock > 0));
    } catch (error) {
      console.error('Error loading products:', error);
      alert('Error al cargar productos');
    } finally {
      setLoadingProducts(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductId || !quantity || parseInt(quantity) <= 0) {
      alert('Por favor complete todos los campos correctamente');
      return;
    }

    const selectedProduct = products.find(p => p.id === selectedProductId);
    if (selectedProduct && parseInt(quantity) > selectedProduct.stock) {
      alert(`La cantidad no puede ser mayor al stock disponible (${selectedProduct.stock})`);
      return;
    }

    setLoading(true);
    try {
      await api.post('/inventory/remove-pieces', {
        product_id: selectedProductId,
        quantity: parseInt(quantity),
        notes: notes || 'Sin motivo especificado',
      });
      onSuccess();
      handleClose();
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Error al sacar piezas';
      alert(message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setSelectedProductId('');
    setQuantity('');
    setNotes('');
    onClose();
  };

  if (!isOpen) return null;

  const selectedProduct = products.find(p => p.id === selectedProductId);
  const maxQuantity = selectedProduct ? selectedProduct.stock : 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold mb-4" style={{ color: '#2e4354' }}>
          Sacar Piezas del Inventario
        </h2>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1" style={{ color: '#2e4354' }}>
              Producto *
            </label>
            {loadingProducts ? (
              <div className="text-sm text-gray-500">Cargando productos...</div>
            ) : (
              <select
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value ? parseInt(e.target.value) : '')}
                className="w-full rounded-lg px-3 py-2 border-2"
                style={{ borderColor: 'rgba(46, 67, 84, 0.2)' }}
                required
              >
                <option value="">Seleccione un producto</option>
                {products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.name} {product.codigo ? `(${product.codigo})` : ''} - Stock: {product.stock}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-1" style={{ color: '#2e4354' }}>
              Cantidad *
            </label>
            <input
              type="number"
              min="1"
              max={maxQuantity}
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="w-full rounded-lg px-3 py-2 border-2"
              style={{ borderColor: 'rgba(46, 67, 84, 0.2)' }}
              required
            />
            {selectedProduct && (
              <div className="text-xs mt-1" style={{ color: '#2e4354', opacity: 0.7 }}>
                Stock disponible: {selectedProduct.stock}
              </div>
            )}
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-1" style={{ color: '#2e4354' }}>
              Motivo / Notas *
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full rounded-lg px-3 py-2 border-2"
              style={{ borderColor: 'rgba(46, 67, 84, 0.2)' }}
              rows={3}
              required
              placeholder="Ej: Daño, Pérdida, Venta especial, etc."
            />
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 rounded-lg font-medium transition-all"
              style={{ backgroundColor: '#f0f7f7', color: '#2e4354' }}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 rounded-lg font-medium text-white transition-all disabled:opacity-50"
              style={{ backgroundColor: '#ef4444' }}
            >
              {loading ? 'Procesando...' : 'Sacar Piezas'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

