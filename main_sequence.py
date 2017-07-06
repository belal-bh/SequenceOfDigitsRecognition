import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt

from prepare_dataset import load_dataset
from sequence import Sequence


def get_batch(dataset, inputs_placeholder, labels_placeholder, keep_prob_placeholder, keep_prob_val):
    if "position" not in dataset:
        dataset["position"] = 0
    position = dataset["position"]
    steps_per_epoch = len(dataset['examples']) // 50
    inputs = dataset['examples'][50 * position: (50 * position) + 50]
    labels = dataset['labels'][50 * position: (50 * position) + 50]
    position += 1
    if position == steps_per_epoch:
        position = 0
    dataset["position"] = position
    return {inputs_placeholder: inputs, labels_placeholder: labels, keep_prob_placeholder: keep_prob_val}


def show_predictions(inference_operation, batch, session, inputs_placeholder):
    logits = session.run(inference_operation, feed_dict=batch)
    argmax = np.argmax(logits, axis=2)
    plt.imshow(batch[inputs_placeholder][0], cmap='gray')
    plt.title(argmax[0])
    plt.show()


def evaluate(dataset, session, operation, inputs_placeholder, labels_placeholder, keep_prob_placeholder, name,
             summary_writer,
             learning_step):
    steps_per_epoch = len(dataset['examples']) // 50
    number_of_examples = steps_per_epoch * 50

    correct_num = 0
    for step in range(steps_per_epoch):
        batch = get_batch(dataset, inputs_placeholder, labels_placeholder, keep_prob_placeholder, 1)
        correct_num += session.run(operation, feed_dict=batch)

    precision = correct_num / number_of_examples
    summary = tf.Summary()
    summary.value.add(tag='Accuracy_' + name, simple_value=precision)
    summary_writer.add_summary(summary, learning_step)
    print("Accuracy %.3f" % precision)


if __name__ == '__main__':

    # Load model
    train = load_dataset("train.p", False)
    validation = load_dataset("validation.p", False)
    test = load_dataset("test.p", True)

    with tf.Graph().as_default():
        # Wiring
        model = Sequence()
        inputs_placeholder, labels_placeholder, keep_prob_placeholder = model.input_placeholders()
        logits = model.inference(inputs_placeholder, keep_prob_placeholder)
        loss = model.loss(logits, labels_placeholder)
        training = model.training(loss, 0.0001)
        evaluation = model.evaluation(logits, labels_placeholder)

        # Initialization
        session = tf.InteractiveSession()
        init = tf.global_variables_initializer()
        session.run(init)

        # visualize graph
        writer = tf.summary.FileWriter("visualizations/" + model.get_name())
        writer.add_graph(session.graph)

        # Summaries
        merged_summary = tf.summary.merge_all()

        # Training
        for step in range(10000 + 1):
            batch = get_batch(train, inputs_placeholder, labels_placeholder, keep_prob_placeholder, 0.5)
            loss_value, summary, _ = session.run([loss, merged_summary, training], feed_dict=batch)
            writer.add_summary(summary, step)
            if step % 1000 == 0:
                print("Step %d, loss %.3f" % (step, loss_value))
                print("Train accuracy")
                evaluate(train, session, evaluation, inputs_placeholder, labels_placeholder, keep_prob_placeholder,
                         "train", writer,
                         step, )
                print("Validation accuracy")
                evaluate(validation, session, evaluation, inputs_placeholder, labels_placeholder, keep_prob_placeholder,
                         "validation", writer,
                         step)
                print("Test accuracy")
                evaluate(test, session, evaluation, inputs_placeholder, labels_placeholder, keep_prob_placeholder,
                         "test", writer,
                         step)
                print()