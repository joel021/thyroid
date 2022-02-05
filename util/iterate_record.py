import tensorflow as tf

row_dataset = tf.data.TFRecordDataset("train.tfrecord")

i = 0
for row_record in row_dataset.take(1):
    example = tf.train.Example()
    example.ParseFromString(row_record.numpy())
    print(example)

    i = i+1

print(i)
