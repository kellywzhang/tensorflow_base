import tensorflow as tf
import numpy as np
from tensorflow.contrib import learn
import datetime

import tf_helpers
import base_architecture
from base_architecture import BaseNN

# Code based on: https://github.com/dennybritz/cnn-text-classification-tf

FLAGS = base_architecture.getFLAGS()

# Load Data
# =================================================================================

# TODO: LOAD YOUR OWN DATA
from tensorflow.examples.tutorials.mnist import input_data
mnist = input_data.read_data_sets('MNIST_data', one_hot=True)

x_dev, y_dev = mnist.validation.next_batch(5000)

# Helper Functions
# =================================================================================
def train_step(x_batch, y_batch, current_step, writer=None, print_bool=False):
	"""
	Single training step
	"""
	feed_dict = {
		nn.input_x: x_batch,
		nn.input_y: y_batch
		# ADD ANY ADDITION INPUTS HERE
	}
	_, summaries, loss_val, accuracy_val = sess.run([train_op, train_summary_op, nn.loss, nn.accuracy], feed_dict)

	time_str = datetime.datetime.now().isoformat()
	if print_bool:
		print("\nTrain: {}: step {}, loss {:g}, acc {:g}".format(time_str, current_step, loss_val, accuracy_val))
	if writer:
		writer.add_summary(summaries, current_step)

	return (loss_val, accuracy_val)

def dev_step(x_batch, y_batch, current_step, writer=None):
	"""
	Evaluates model on a validation set
	"""
	feed_dict = {
		nn.input_x: x_batch,
		nn.input_y: y_batch,
		# ADD ANY ADDITION INPUTS HERE
	}
	summaries, loss_val, accuracy_val = sess.run([dev_summary_op, nn.loss, nn.accuracy], feed_dict)

	time_str = datetime.datetime.now().isoformat()
	print("Dev:   {}: step {}, loss {:g}, acc {:g}".format(time_str, current_step, loss_val, accuracy_val))
	if writer:
		writer.add_summary(summaries, current_step)

	return (loss_val, accuracy_val)

# Starting Session
# ================================================================================
sess = tf.InteractiveSession()
nn = BaseNN( # TODO: DEFINE YOUR OWN NETWORK
		input_dim=784,
		output_dim=10,
		num_nodes=0,
		l2_reg_lambda=0
	) 

optimizer = tf.train.AdamOptimizer(FLAGS.learning_rate) # TODO: CHOOSE YOUR FAVORITE OPTIMZER
global_step = tf.Variable(0, name='global_step', trainable=False)
grads_and_vars = optimizer.compute_gradients(nn.loss)
train_op = optimizer.apply_gradients(grads_and_vars, global_step=global_step)

train_summary_op, dev_summary_op, train_summary_writer, dev_summary_writer, timestamp, checkpoint_prefix = \
	tf_helpers.save_summaries(sess, nn.loss, nn.accuracy, grads_and_vars, FLAGS)
saver = tf.train.Saver(tf.all_variables())

# Training and Validation
# ===============================================================================
sess.run(tf.initialize_all_variables())

# TODO: SETUP YOUR DATA'S BATCHES
#batches = data_helpers.batch_iter(
#	list(zip(x_train, y_train)), FLAGS.batch_size, FLAGS.num_epochs)

def loss_early_stopping():
	min_loss = 999999999
	increasing_loss_count = 0
	max_accuracy = 0
	max_accuracy_step = 0

	for batch in batches:
		x_batch, y_batch = zip(*batch) # TODO: SETUP YOUR DATA'S BATCHES

		current_step = tf.train.global_step(sess, global_step)
		if current_step % FLAGS.evaluate_every == 0:
			train_loss, train_accuracy = train_step(x_batch, y_batch, current_step, print_bool=True)
			dev_loss, dev_accuracy = dev_step(x_dev, y_dev, current_step)

			if dev_loss < min_loss:
				min_loss = dev_loss
				increasing_loss_count = 0
			else:
				increasing_loss_count += 1

			if dev_accuracy > max_accuracy:
				max_accuracy = dev_accuracy
				max_accuracy_step = current_step

			if current_step > FLAGS.patience and FLAGS.patience_increase < increasing_loss_count:
				break

		else:
			train_loss, train_accuracy = train_step(x_batch, y_batch, current_step, print_bool=False)

		if current_step % FLAGS.checkpoint_every == 0:
			path = saver.save(sess, checkpoint_prefix, global_step=global_step)
			print("Saved model checkpoint to {}".format(path))

	return (train_loss, train_accuracy, max_accuracy, max_accuracy_step)

def accuracy_early_stopping():
	max_accuracy = 0
	max_accuracy_step = 0

	#for batch in batches:
		#x_batch, y_batch = zip(*batch) # TODO: SETUP YOUR DATA'S BATCHES

	for _ in range(1000):
		x_batch, y_batch = mnist.train.next_batch(FLAGS.batch_size)

		current_step = tf.train.global_step(sess, global_step)
		if current_step % FLAGS.evaluate_every == 0:
			train_loss, train_accuracy = train_step(x_batch, y_batch, current_step, print_bool=True)
			dev_loss, dev_accuracy = dev_step(x_dev, y_dev, current_step)

			if dev_accuracy > max_accuracy:
				max_accuracy = dev_accuracy
				max_accuracy_step = current_step

			if current_step > FLAGS.patience and FLAGS.patience_increase < current_step - max_accuracy_step:
				break

		else:
			train_loss, train_accuracy = train_step(x_batch, y_batch, current_step, print_bool=False)

		if current_step % FLAGS.checkpoint_every == 0:
			path = saver.save(sess, checkpoint_prefix, global_step=global_step)
			print("Saved model checkpoint to {}".format(path))

	return (train_loss, train_accuracy, max_accuracy, max_accuracy_step)

train_loss, train_accuracy, max_accuracy, max_accuracy_step = accuracy_early_stopping()

print("\nFinal Valildation Evaluation:")
current_step = tf.train.global_step(sess, global_step)
dev_loss, dev_accuracy = dev_step(x_dev, y_dev, current_step, writer=dev_summary_writer)
print("Maximum validation accuracy at step {}: {}".format(max_accuracy_step, max_accuracy))
print("")

tf_helpers.write_results(current_step, train_loss, train_accuracy, dev_loss, dev_accuracy, timestamp)

sess.close()

