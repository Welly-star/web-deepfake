import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

# ===================================================================
# SCRIPT TRANSFER LEARNING RESNET-50 UNTUK AKURASI MAKSIMAL
# ===================================================================

def build_resnet50_model():
    # 1. Load Pre-trained ResNet50 (tanpa layer output/top)
    # Weights 'imagenet' sangat penting untuk Transfer Learning
    base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    
    # 2. Freeze base model agar weight ImageNet tidak rusak saat awal training
    for layer in base_model.layers:
        layer.trainable = False
        
    # 3. Tambahkan Custom Head untuk klasifikasi Real vs Deepfake (Binary)
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(512, activation='relu')(x)
    x = Dropout(0.5)(x) # Dropout untuk mencegah Overfitting
    x = Dense(128, activation='relu')(x)
    predictions = Dense(1, activation='sigmoid')(x) # Sigmoid untuk 2 class (Real/Fake)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    
    # 4. Compile Model (Learning rate kecil untuk transfer learning)
    model.compile(optimizer=Adam(learning_rate=0.001), 
                  loss='binary_crossentropy', 
                  metrics=['accuracy'])
    return model, base_model

def train_model(train_dir, val_dir):
    # Augmentasi Data: Sangat krusial agar model kebal terhadap variasi foto dan akurat!
    # Menggunakan fungsi preprocessing bawaan ResNet50
    train_datagen = ImageDataGenerator(
        preprocessing_function=tf.keras.applications.resnet50.preprocess_input,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.15,
        zoom_range=0.15,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    
    val_datagen = ImageDataGenerator(
        preprocessing_function=tf.keras.applications.resnet50.preprocess_input
    )

    train_generator = train_datagen.flow_from_directory(
        train_dir, target_size=(224, 224), batch_size=32, class_mode='binary')
        
    val_generator = val_datagen.flow_from_directory(
        val_dir, target_size=(224, 224), batch_size=32, class_mode='binary')

    model, base_model = build_resnet50_model()

    # Callbacks untuk mengoptimalkan training dan menyimpan model paling akurat
    checkpoint = ModelCheckpoint('resnet50_deepfake_model.h5', monitor='val_accuracy', save_best_only=True, mode='max', verbose=1)
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=1e-6)

    print("Mulai Fase 1: Training Custom Head...")
    history = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=10,
        callbacks=[checkpoint, early_stop, reduce_lr]
    )

    # FASE 2: FINE-TUNING (Membuka sebagian layer ResNet untuk meningkatkan akurasi spesifik Deepfake)
    print("Mulai Fase 2: Fine-Tuning untuk Akurasi Maksimal...")
    for layer in base_model.layers[-30:]: # Unfreeze 30 layer terakhir
        layer.trainable = True
        
    model.compile(optimizer=Adam(learning_rate=1e-5), # Learning rate sangat kecil agar tidak merusak bobot
                  loss='binary_crossentropy', 
                  metrics=['accuracy'])

    history_finetune = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=10,
        callbacks=[checkpoint, early_stop, reduce_lr]
    )
    
    print("Training Selesai! Model paling akurat disimpan sebagai 'resnet50_deepfake_model.h5'")

if __name__ == '__main__':
    # CARA MENGGUNAKAN:
    # Buat folder 'dataset/train' dan 'dataset/val'
    # Di dalam masing-masing folder, buat folder 'REAL' dan 'DEEPFAKE' berisi foto-fotonya
    # Lalu jalankan script ini.
    print("Pastikan folder dataset sudah diatur dengan benar sebelum menjalankan.")
    # train_model('dataset/train', 'dataset/val')

