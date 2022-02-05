import tensorflow as tf



inputs = tf.keras.layers.Input(shape=(528,528,3))

x1 = tf.keras.layers.Conv2D(8, (7,7))(inputs)
x1 = tf.keras.layers.BatchNormalization()(x1)
x1 = tf.nn.relu(x1)

x1 = tf.keras.layers.MaxPool2D((2,2))(x1)
x1 = tf.keras.layers.DepthwiseConv2D(activation='relu', kernel_size=(7,7))(x1)
x1 = tf.keras.layers.Conv2D(12, (7,7), activation='relu')(x1)
x1 = tf.keras.layers.MaxPool2D((2,2))(x1)

x1 = tf.keras.layers.DepthwiseConv2D(activation='relu', kernel_size=(7,7))(x1)
x1 = tf.keras.layers.BatchNormalization()(x1)
x1 = tf.keras.layers.MaxPool2D((2,2))(x1)

x1 = tf.keras.layers.Conv2D(16, (7,7))(x1)
x1 = tf.keras.layers.BatchNormalization()(x1)
x1 = tf.nn.relu(x1)
x1 = tf.keras.layers.MaxPool2D((2,2))(x1)

x1 = tf.keras.layers.DepthwiseConv2D((7,7))(x1)
x1 = tf.keras.layers.BatchNormalization()(x1)
x1 = tf.nn.relu(x1)
x1 = tf.keras.layers.MaxPool2D((2,2))(x1)

x2 = tf.keras.layers.Conv2D(18, (5,5))(x1)
x2 = tf.keras.layers.BatchNormalization()(x2)
x2 = tf.nn.relu(x2)
x2 = tf.keras.layers.MaxPool2D((2,2))(x2)

x3 = tf.keras.layers.Conv2D(18, (5,5), (2,2))(x1)
#x3 = tf.keras.layers.ZeroPadding2D((1,1))(x3)
x3 = tf.keras.layers.BatchNormalization()(x3)
x3 = tf.nn.relu(x3)

x = tf.keras.layers.add([x2,x3])
x = tf.keras.layers.Flatten()(x)
x = tf.keras.layers.Dense(1, activation='sigmoid')(x)
model = tf.keras.Model(inputs, x)

model.summary()



